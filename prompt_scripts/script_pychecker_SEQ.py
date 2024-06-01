"""
Description :   The prompt script for pychecker's workflow on SEQ circuits. The WF_pychecker_SEQ script is only used in preliminary experiments. The final verion of pychecker is in WF_pychecker script, including a CMB/SEQ discriminator.
Author      :   AutoBench's Author (Anonymous Email)
Time        :   2024/3/22 10:40:43
LastEdited  :   2024/4/30 23:37:45
"""

from .base_script import BaseScript, BaseScriptStage
from . import public_stages
from . import utils
from .utils import given_TB
# from .public_stages import StageChecklist
import json

class WF_pychecker_SEQ(BaseScript):
    """
    WF_pychecker_SEQ
    """
    def __init__(self, prob_data:dict, task_dir:str, config:object):
        super().__init__(prob_data, task_dir, config)
        self.max_check_iter = self.config.autoline.checklist.max
        self.py_code = ""
        self.py_debug_focus = True # only for SEQ

    def make_and_run_stages(self):
        # stage0
        self.stage0 = Stage0(self.prob_data, **self.gptkwargs)
        self.stage_operation(self.stage0)
        # stage1
        self.stage1 = public_stages.Stage1(self.prob_data, **self.gptkwargs)
        self.stage_operation(self.stage1)
        # stage2
        self.stage2 = public_stages.Stage2(self.prob_data, self.stage1.response, **self.gptkwargs)
        self.stage_operation(self.stage2)
        # stage3
        self.stage3 = Stage3(self.prob_data, self.stage1.response, self.stage2.response, **self.gptkwargs)
        self.stage_operation(self.stage3)
        # stage4
        self.stage4 = Stage4_SEQ(self.prob_data, self.stage1.response, self.stage2.response, **self.gptkwargs)
        self.stage_operation(self.stage4)
        # stagechecklist
        self.stagecheck = StageChecklist(self.TB_code, self.stage2.response, self.max_check_iter, **self.gptkwargs)
        self.stage_operation(self.stagecheck)
        # stage4b
        self.stage4b = Stage4b_SEQ(self.prob_data, self.TB_code, **self.gptkwargs)
        self.stage_operation(self.stage4b)
        # stage5
        self.stage5 = Stage5_SEQ(self.prob_data, self.stage1.response, self.stage3.response, **self.gptkwargs)
        self.stage_operation(self.stage5) 


    def make_and_run_reboot_stages(self, debug_dir):
        if self.reboot_mode == "TB":
            # stage4
            self.stage4 = Stage4_SEQ(self.prob_data, self.stage1.response, self.stage2.response, **self.gptkwargs)
            self.stage_operation(self.stage4, debug_dir, reboot_en=True)
            # stagechecklist
            self.stagecheck = StageChecklist(self.TB_code, self.stage2.response, self.max_check_iter, **self.gptkwargs)
            self.stage_operation(self.stagecheck, debug_dir, reboot_en=True)
            # stage4b
            self.stage4b = Stage4b_SEQ(self.prob_data, self.TB_code, **self.gptkwargs)
            self.stage_operation(self.stage4b, debug_dir, reboot_en=True)
        elif self.reboot_mode == "PY":
            # stage5
            self.stage5 = Stage5_SEQ(self.prob_data, self.stage1.response, self.stage3.response, **self.gptkwargs)
            self.stage_operation(self.stage5, debug_dir, reboot_en=True)
        else:
            raise ValueError("invalid reboot_mode in WF_pychecker script (circuit type: SEQ)")
        
class Stage0(BaseScriptStage):
    def __init__(self, prob_data, **gptkwargs) -> None:
        super().__init__("stage_0", **gptkwargs)
        self.prob_data = prob_data
        self.circuit_type = None
        
    def make_prompt(self):
        self.add_prompt_line("Please generate the verilog RTL code according to the following description and header information:")
        self.add_prompt_line("problem description:")
        self.add_prompt_line(self.prob_data["description"])
        self.add_prompt_line("RTL header:")
        self.add_prompt_line(self.prob_data["header"])
        self.add_prompt_line("please only reply verilog codes, no other words.")

    def postprocessing(self):
        self.response = self.extract_code(self.response, "verilog")[-1]
        self.circuit_type = utils.circuit_type_by_code(self.response)

SIGNALTEMP_PLACEHOLDER_1 = "/* SIGNAL TEMPLATE 1 */"
SIGNALTEMP_PLACEHOLDER_1A = "/* SIGNAL TEMPLATE 1A */"
SIGNALTEMP_PLACEHOLDER_1B = "/* SIGNAL TEMPLATE 1B */"

STAGE3_TXT1="""1. Your task is to write a verilog testbench for an verilog RTL module code (we call it as "DUT", device under test). The information we have is the problem description that guides student to write the RTL code (DUT) and the header of the "DUT". Our target is to generate the verilog testbench for the DUT. This testbench can check if the DUT in verilog satisfies all technical requirements of the problem description.
2. you are in stage 3; in this stage, please give me the core rules of an ideal DUT. you should give these rules in python. (For convenience, you can use binary or hexadecimal format in python, i.e. 0b0010 and 0x1a). Later we will use these ideal rules to generate expected values in each test scenario. currently you must only generate the core part of the rules. the input of these rules should be related to the test vectors from test scenario. the rule should give the expected values under test vectors. You don't need to consider the control signals like clk or reset, unless the core rules of this task are about these signals. You can use numpy, scipy or other third party python libraries to help you write the rules. Please import them if you need. 
3. your information is:"""

class Stage3(BaseScriptStage):
    def __init__(self, prob_data, response_stage1, response_stage2, **gptkwargs) -> None:
        super().__init__("stage_3", **gptkwargs)
        self.prob_data = prob_data
        self.response_stage1 = response_stage1
        self.response_stage2 = response_stage2
        self.txt1 = STAGE3_TXT1

    def make_prompt(self):
        self.prompt = ""
        self.add_prompt_line(self.txt1)
        # problem description
        self.add_prompt_line("RTL circuit problem description:")
        self.add_prompt_line(self.prob_data["description"])
        # specification
        self.add_prompt_line("RTL testbench specification:")
        self.add_prompt_line(self.response_stage1)
        # DUT header
        self.add_prompt_line("DUT header:")
        self.add_prompt_line(self.prob_data["header"])
        # test scenarios
        self.add_prompt_line("test scenario: (please note the test vectors below, it will help you determine the input parameters of the rules)")
        self.add_prompt_line(self.response_stage2)
        # end
        self.add_prompt_line("your response should only contain python code. For convenience, you can use binary or hexadecimal format in python. For example: 0b0010 and 0x1a")

    def postprocessing(self):
        # extract python codes; codes may be more than one
        python_codes = self.extract_code(self.response, "python")
        response = ""
        for python_code in python_codes:
            response += python_code + "\n"
        self.response = response
    
def header_to_SignalTxt_template(header:str, template_scenario_idx:str="1", signal_value:str="0"):
    """
    - header: the header of DUT
    - template_scenario_idx: the scenario index in the template
    - signal_value: the value of the signal in the template
    - only: None: both input signal and output signal; "input": only input signal; "output": only output signal
    - from header to signals in txt
    - for the automatic generation of signals in testbench
    - target: given the DUT header, generate the signal output template
    - eg: if we have a DUT header like "module DUT(input a, b, c, output d, e);", the signal output template should be like "scenario: 1, a = 1, b = 0, c = 1, d = 0, e = 0"
    """
    signals = header.split("(")[1].split(")")[0].split(",")
    # remove the "input" and "output" keywords
    signals = [signal.strip().split(" ")[-1] for signal in signals]
    # generate the signal output template
    signal_out = "scenario: " + template_scenario_idx
    for signal in signals:
        signal_out += f", {signal} = {signal_value}"
    return signal_out

STAGE4_SEQ_TXT1 = """
1. Your task is to complete a given verilog testbench code. This testbench is for a verilog RTL module code (we call it as "DUT", device under test). This circuit is a sequential circuit. The infomation we have is 
- 1.1. the problem description that guides student to write the RTL code (DUT) and the header of the "DUT". 
- 1.2. the module header.
- 1.3. test scenarios which determines values and sequential information of test vectors
- 1.4. the testbench structure
- 1.5. the instruction of writing our testbench
"""

# STAGE4_SEQ_INSTR = """
# The design Instruction is:
# you should display the signals every clock cycle (#10). When it is time to check the output value of DUT, add [check] at the beginning of the output line
# There is a example code (partial) for a DFF circuit:
# exmaple (1):
# ```
# // the input of DFF is "d", the output of DFF is "q", the clock signal is "clk"
# // scenario 1: test the function of DUT:
# scenario = 1;
# d = 1; $fdisplay(file, "scenario: 1, clk = %%d, d = %%d, q = %%d", clk, d, q); // set the input signal, display
# #10;
# $fdisplay(file, "[check]scenario: 1, clk = %%d, d = %%d, q = %%d", clk, d, q); // check the output signal, display
# #10;
# // scenario 2
# scenario = 2;
# d = 0; $fdisplay(file, "scenario: 2, clk = %%d, d = %%d, q = %%d", clk, d, q); 
# #10;
# $fdisplay(file, "[check]scenario: 2, clk = %%d, d = %%d, q = %%d", clk, d, q); 
# #10;
# ...
# ```
# example (2):
# for a scenario that needs multiple clock cycles before checking, the example code is like this:
# ```
# // scenario 3: multiple clock cycles before checking
# scenario = 3
# d = 1; $fdisplay(file, "scenario: 3, clk = %%d, d = %%d, q = %%d", clk, d, q); 
# #10;
# repeat(5) begin
#     $fdisplay(file, "scenario: 3, clk = %%d, d = %%d, q = %%d", clk, d, q); 
#     #10;
# end
# $fdisplay(file, "[check]scenario: 3, clk = %%d, d = %%d, q = %%d", clk, d, q); 
# #10;
# ```
# for a scenario that has many checking time points, the example code is like this:
# ```
# // scenario 4: multi checking points
# scenario = 4;
# d = 1; $fdisplay(file, "scenario: 4, clk = %%d, d = %%d, q = %%d", clk, d, q); 
# #10;
# repeat(5) begin
#     $fdisplay(file, "[check]scenario: 4, clk = %%d, d = %%d, q = %%d", clk, d, q); 
#     #10;
# end
# ```
# (3) the signals you save is the input and output of DUT, you should determine the signals according to DUT's header
# """ # not used currently


# STAGE4_SEQ_TXT2 = r"""
# The testbench does not need to check the DUT's output but only export the signals of DUT. Please determine the input signal's exact values according to given test scenarios. please only complement the last initial code part. your code should begin from the "initial begin..." part to "end". You must use %d when exporting values.
# """
STAGE4_SEQ_TXT2 = """
The testbench does not need to check the DUT's output but only export the signals of DUT. Please export the signals of DUT to a file named "TBout.txt" at the end of each scenario. The template is given below:
%s
The variables are already declared. The clock signal is already prepared. This output will be used to check the correctness of the DUT's output later.
please only use "#10" as the delay when you need. If you need longer delay, you can use multiple "#10", such as "#10; #10; #10;". Avoid meaningless long delay in your code.
If you need a loop in a scenario to check multiple time points, use "repeat" loop. for exmaple:
```
// scenario x
scenario = x;
signal_1 = 1;
repeat(5) begin
    %s
    #10;
end
```
Please determine the input signal's exact values according to given test scenarios. 
Note: please complete the last initial code part (marked in the given testbench template). You should give me the completed full code. The testbench template above is to help you generate the code. You must use %%d when exporting values.
please generate the full testbench code. please only reply verilog codes, no other words. 
"""%(SIGNALTEMP_PLACEHOLDER_1, SIGNALTEMP_PLACEHOLDER_1)
class Stage4_SEQ(BaseScriptStage):
    """stage 4 (SEQ): generate the testbench that export the signals of DUT to a file"""
    def __init__(self, prob_data, response_stage1, response_stage2, **gptkwargs) -> None:
        super().__init__("stage_4", **gptkwargs)
        self.prob_data = prob_data
        self.response_stage1 = response_stage1
        self.response_stage2 = response_stage2
        signals_output_template = self.header_to_SignalTxt_template(prob_data["header"], check_en=True)
        # self.txt_instruction = STAGE4_SEQ_INSTR.replace(SIGNALTEMP_PLACEHOLDER_1, signals_input_template).replace(SIGNALTEMP_PLACEHOLDER_1A, signals_output_template)
        self.txt1 = STAGE4_SEQ_TXT1
        self.txt2 = STAGE4_SEQ_TXT2.replace(SIGNALTEMP_PLACEHOLDER_1, signals_output_template)
        self.TB_code_object = given_TB(prob_data["header"])
        # signal_template_scenario = signals_input_template + "\n" + signals_input_template + "\n" + signals_input_template + "\n" + signals_output_template

    def make_prompt(self):
        self.prompt = ""
        self.add_prompt_line(self.txt1)
        # DUT header
        self.add_prompt_line("DUT header:")
        self.add_prompt_line(self.prob_data["header"])
        # other information:
        self.add_prompt_line("Your other information:")
        # problem description
        self.add_prompt_line("RTL circuit problem description:")
        self.add_prompt_line(self.prob_data["description"])
        # scenarios
        self.add_prompt_line("IMPORTANT - test scenario (Please determine the values of input signals according to these test scenarios.):")
        self.add_prompt_line(self.response_stage2)
        # given codes
        self.add_prompt_line("below is the given testbench codes:")
        self.add_prompt_line(self.TB_code_object.gen_template())
        # end
        self.add_prompt_line(self.txt2)

    def postprocessing(self):
        # verilog codes
        self.response = self.extract_code(self.response, "verilog")[-1]
        # self.TB_code_object.TB_code_test = self.response
        # self.TB_code_out = self.TB_code_object.gen_template()
        self.TB_code_out = self.response
        self.TB_code_out = utils.verilog_patch(self.TB_code_out)

    @staticmethod
    def header_to_SignalTxt_template(header:str, check_en = False):
        """
        - header: the header of DUT
        - template_scenario_idx: the scenario index in the template
        - signal_value: the value of the signal in the template
        - only: None: both input signal and output signal; "input": only input signal; "output": only output signal
        - from header to signals in txt
        - for the automatic generation of signals in testbench
        - target: given the DUT header, generate the signal output template
        - eg: if we have a DUT header like "module DUT(input clk, load, data, output q);", the signal output template should be like "$fdisplay(file, "scenario: %d, clk = %d, load = %d, data = %d, q = %d", scenario, clk, load, data, q);"
        """
        signals = utils.extract_signals(header)
        # generate ", clk = %d, load = %d, data = %d, q = %d"
        signal_form1 = ""
        signal_form2 = ""
        for signal in signals:
            signal_form1 += f", {signal['name']} = %d"
            signal_form2 += f", {signal['name']}"
        if check_en:
            txt = r'$fdisplay(file, "[check]scenario: %d' + signal_form1 + r'", scenario' + signal_form2 + r');'
        else:
            txt = r'$fdisplay(file, "scenario: %d' + signal_form1 + r'", scenario' + signal_form2 + r');'
        return txt


        
Stage4b_SEQ_TXT1 = """given the scenario based verilog testbench code below:"""
Stage4b_SEQ_TXT2 = """
please help me to export the input of DUT module by using code below:

[IMPORTANT]:
%s

you should insert the code above into scenario checking part. In each scenario, you should insert the code above after the input of DUT module changed. Don't delete the existing $display codes.

For example, for a circuit that has two input signals changed at different times in one scenario, the original code is like this:
- original code:
// scenario 1 begins
scenario = 1;
signal_1 = 1; 
// insert $fdisplay here
#10; 
signal_2 = 1; 
// insert $fdisplay here
#10; 
$fdisplay(file, "[check]scenario: %%d, signal_1 = %%d, signal_2 = %%d", scenario, signal_1, signal_2); // this should be reserved. Never change the existing codes.
#10;
// scenario 1 ends

- after insertion:
// scenario 1 begins
scenario = 1;
signal_1 = 1;  
$fdisplay(file, "scenario: %%d, signal_1 = %%d, signal_2 = %%d", scenario, signal_1, signal_2); 
#10;
signal_2 = 1;  
$fdisplay(file, "scenario: %%d, signal_1 = %%d, signal_2 = %%d", scenario, signal_1, signal_2); 
#10;
$fdisplay(file, "[check]scenario: %%d, signal_1 = %%d, signal_2 = %%d", scenario, signal_1, signal_2);
#10;
// scenario 1 ends

please insert codes according to the rules above. DO NOT modify other codes! please reply the modified full codes. please only reply verilog codes, no other words."""%(SIGNALTEMP_PLACEHOLDER_1)
class Stage4b_SEQ(BaseScriptStage):
    def __init__(self, prob_data, TB_code, **gptkwargs) -> None:
        super().__init__("stage_4b", **gptkwargs)
        self.header = prob_data["header"]
        signals_input_template = Stage4_SEQ.header_to_SignalTxt_template(prob_data["header"], check_en=False)
        self.TB_code = TB_code
        self.txt1 = Stage4b_SEQ_TXT1
        self.txt2 = Stage4b_SEQ_TXT2.replace(SIGNALTEMP_PLACEHOLDER_1, signals_input_template)
        self.TB_code_out = self.TB_code

    def make_prompt(self):
        self.prompt = ""
        self.add_prompt_line(self.txt1)
        self.add_prompt_line(self.TB_code)
        self.add_prompt_line(self.txt2)
        
    def postprocessing(self):
        self.TB_code_out = self.extract_code(self.response, "verilog")[-1]
        self.TB_code_out = utils.pychecker_SEQ_TB_standardization(self.TB_code_out, self.header)

STAGE5_SEQ_TXT1 = """
1. background: Your task is to verify the functional correctness of a verilog RTL module code (we call it as "DUT", device under test). This module is a sequential circuit. Our plan is to first export the signals (input and output) of the DUT under test scenarios. Then, we will use a python script to check the correctness of DUT.
2. You are in stage 5. In this stage, we already exported the signals of DUT. The signals are like below: (the signal names are real, but the values are just for example, clock signals are not included, each vector represents a new clock cycle)
%s
Here's the explanation of some special signals in signal vectors: 
- "scenario": The "scenario" is not DUT's signal but to tell you the current scenario index. 
- "check_en": The "check_en" signal is not from the DUT. "Check_en" is a bool value to tell you this is the time to check the output of DUT. It is related to the class method "check" (we will explain it later). After checking the output, a new scenario will start.
3. Your current task is: write a python class "GoldenDUT". This python class can represent the golden DUT (the ideal one). In your "GoldenDUT", you should do the following things:
- 3.1. write a method "def __init__(self)". Set the inner states/values of the golden DUT. These values have suffix "_reg". The initial value of these inner values is "x", but later will be digits. The "__init__" method has no input parameters except "self".
- 3.2. write a method "def load(self, signal_vector)". This method is to load the important input signals and the inner values of "GoldenDUT" shall change according to the input signals. There is no clock signal in the input signal vector, every time the "load" method is called, it means a new clock cycle. The initial values "x" should be changed according to the input signals. This method has no return value.
- 3.3. write a method "def check(self, signal_vector)". This method is to determine the expected output values and compare them with output signals from DUT. It should return True or False only. If return false, please print the error message. Hint: you can use code like "print(f"Scenario: {signal_vector['scenario']}, expected: a={a_reg}, observed a={a_observed}")" to print, suppose "a" is the output signal's name.
- 3.4. write other methods you need, they can be called by "load" or "check".
- 3.5. the input of "load" and "check" is the signal vector. The signal vector is a dictionary, the key is the signal name, the value is the signal value.
4. Other information:
- You can use binary (like 0x1101), hexadecimal (like 0x1a) or normal number format in python.
- if the bit width of one variable is limited, use bit mask to assure the correctness of the value.
- you can import numpy, math, scipy or other python libraries to help you write the python class.
5. You have the information below to help you check the correctness of DUT:
"""%(SIGNALTEMP_PLACEHOLDER_1)

STAGE5_SEQ_TXT2 = """
[IMPORTANT]
I will repeat the important information: 
3. Your current task is: write a python class "GoldenDUT". This python class can represent the golden DUT (the ideal one). In your "GoldenDUT", you should do the following things:
- 3.1. write a method "def __init__(self)". Set the inner states/values of the golden DUT. These values have suffix "_reg". The initial value of these inner values should be digits. You can set the initial values according to information or just "0"s. The "__init__" method has no input parameters except "self".
- 3.2. write a method "def load(self, signal_vector)". This method is to load the important input signals and the inner values of "GoldenDUT" shall change according to the input signals. There is no clock signal in the input signal vector, every time the "load" method is called, it means a new clock cycle. The initial values "x" should be changed according to the input signals. This method has no return value.
- 3.3. write a method "def check(self, signal_vector)". This method is to determine the expected output values and compare them with output signals from DUT. It should return True or False only. If return false, please print the error message. Hint: you can use code like "print(f"Scenario: {signal_vector['scenario']}, expected: a={a_reg}, observed a={a_observed}")" to print, suppose "a" is the output signal's name.  
- 3.4. write other methods you need, they can be called by "load" or "check".
- 3.5. the input of "load" and "check" is the signal vector. The signal vector is a dictionary, the key is the signal name, the value is the signal value.
4. Other information:
- You can use binary (like 0x1101), hexadecimal (like 0x1a) or normal number format in python.
- if the bit width of one variable is limited, use bit mask to assure the correctness of the value.
- you can import numpy, math, scipy or other python libraries to help you write the python class.

please only reply the python codes of the python class. no other words.
"""

STAGE5_SEQ_CODE1 = """
def check_dut(vectors_in):
    golden_dut = GoldenDUT()
    failed_scenarios = []
    for vector in vectors_in:
        if vector["check_en"]:
            check_pass = golden_dut.check(vector)
            if check_pass:
                print(f"Passed; vector: {vector}")
            else:
                print(f"Failed; vector: {vector}")
                failed_scenarios.append(vector["scenario"])
        golden_dut.load(vector)
    return failed_scenarios
"""

STAGE5_SEQ_CODE2 = """
def SignalTxt_to_dictlist(txt:str):
    signals = []
    lines = txt.strip().split("\\n")
    for line in lines:
        signal = {}
        if line.startswith("[check]"):
            signal["check_en"] = True
            line = line[7:]
        elif line.startswith("scenario"):
            signal["check_en"] = False
        else:
            continue
        line = line.strip().split(", ")
        for item in line:
            if "scenario" in item:
                item = item.split(": ")
                signal["scenario"] = item[1].replace(" ", "")
            else:
                item = item.split(" = ")
                key = item[0]
                value = item[1]
                if ("x" not in value) and ("X" not in value) and ("z" not in value):
                    signal[key] = int(value)
                else:
                    if ("x" in value) or ("X" in value):
                        signal[key] = 0 # used to be "x"
                    else:
                        signal[key] = 0 # used to be "z"
        signals.append(signal)
    return signals
with open("TBout.txt", "r") as f:
    txt = f.read()
vectors_in = SignalTxt_to_dictlist(txt)
tb_pass = check_dut(vectors_in)
print(tb_pass)
"""
class Stage5_SEQ(BaseScriptStage):
    """stage 5 (SEQ): generate the pychecker that receive the signals from testbench and check the correctness of DUT"""
    def __init__(self, prob_data, response_stage1, response_stage3, **gptkwargs) -> None:
        super().__init__("stage_5", **gptkwargs)
        self.prob_data = prob_data
        self.response_stage1 = response_stage1 # currently not used
        self.response_stage3 = response_stage3
        self.txt1 = STAGE5_SEQ_TXT1.replace(SIGNALTEMP_PLACEHOLDER_1, utils.signal_dictlist_template(prob_data["header"], exclude_clk=True))
        self.txt2 = STAGE5_SEQ_TXT2
        self.code_tail = STAGE5_SEQ_CODE1 + STAGE5_SEQ_CODE2

    def make_prompt(self):
        self.prompt = ""
        # introduction
        self.add_prompt_line(self.txt1)
        # problem description
        self.add_prompt_line("DUT circuit problem description:")
        self.add_prompt_line(self.prob_data["description"])
        # DUT header
        self.add_prompt_line("The header of DUT (note the input and output signals):")
        self.add_prompt_line(self.prob_data["header"])
        # python rules
        self.add_prompt_line("Here is the basic rules in python for the module. It was generated in previous stage. You can use it as a reference, but you should write your own python script. This is just for your better understanding. You can use them or not in your python class")
        self.add_prompt_line(self.response_stage3)
        # end
        self.add_prompt_line(self.txt2)

    def postprocessing(self):
        # python codes
        self.response = self.extract_code(self.response, "python")[-1]
        self.Pychecker_code_out = self.response + self.code_tail


# class Stage5b_SEQ(BaseScriptStage):
#     def __init__(self, stage_name, **gptkwargs) -> None:
#         super().__init__(stage_name, **gptkwargs)



# STAGE5_SEQ_PYFORMAT = """Your python scritp should contain a function "check_dut", its header is "def check_dut(test_vectors:list) -> bool:". It can also call other functions you write in this script. If all test scenarios passed, function "check_dut" should return an empty list [], otherwise it should return the list of failed scenarios indexes. You can use binary (like 0x1101), hexadecimal (like 0x1a) or normal number format in python.""" # TODO: later this function will also show the failed scenario idx

# STAGE5_SEQ_TXT1 = """
# 1. background: Your task is to verify the functional correctness of a verilog RTL module code (we call it as "DUT", device under test). This module is a sequential circuit. Our plan is to first export the signals (input and output) of the DUT under test scenarios. Then, we will use a python script to check the correctness of DUT.
# 2. You are in stage 5. In this stage, we already exported the signals of DUT. The DUT is a digital sequential circuit. Your task is to write a python script. The python script contains one main function "check_dut" and other functions and classes to be called by "check_dut". The input of "check_dut" is a vector of signals from DUT in the format below: (the signal names are real, but the values are just for example, clock signals are not included, each vector represents a new clock cycle)
# %s
# Here's the explanation of some special signals in signal vectors: 
# - "scenario": The "scenario" is not DUT's signal but to tell you the current scenario index. 
# - "check_en": The "check_en" signal is not from the DUT. "Check_en" is a bool value to tell you this is the time to check the output of DUT. It is related to the class method "check" (we will explain it later). After checking the output, a new scenario will start.
# The main function "check_dut" should check the correctness according to the input signals. The input signals are all in decimal format. It will call other functions and classes to check the correctness of DUT. 
# The DUT is a sequential circuit. It has inner states/values. You can use python class object "golden_DUT" to represent the golden DUT (the ideal one). In your "golden_DUT", you should also set inner states/values. These values have suffix "_reg".  The initial value of these inner values is "x", but later will be digits.
# Your python class "golden_DUT" should has two basic methods: "load" and "check": 
# - "load" method is to load the input signals from vector and the inner values of "golden_DUT" shall change according to the input signals. There is no clock signal in the input signal vector, every time the "load" method is called, it means a new clock cycle.
# - "check" method is to determine the expected output values and compare them with output signals from DUT. Also, it should print the values of them for later debugging.
# - There is another method "input_vector", it will receive one signal vector, if "check_en" is false, it will only run "load"; if "check_en" is true, it will first run "check" method and then run "load" method.
# 3. %s 
# 4. You have the information below to help you check the correctness of DUT:
# """%(SIGNALTEMP_PLACEHOLDER_1, STAGE5_SEQ_PYFORMAT)

# STAGE5_SEQ_TXT2 = """
# [IMPORTANT] %s
# The DUT is a sequential circuit. It has inner states/values. You can use python class object "golden_DUT" to represent the sequential circuit. In your "golden_DUT", you should also set inner states/values. These values have suffix "_reg".  The initial value of these inner values is "x", but later will be digits. 
# Your python class should has two basic methods: "load" and "check": 
# - "load" method is to load the input signals from vector and the inner values of "golden_DUT" shall change according to the input signals. 
# - "check" method is to determine the expected output values and compare them with output signals from DUT. Also, it should print the values of them for later debugging.
# - There is another method "input_vector", it will receive one signal vector, if "check_en" is false, it will only run "load"; if "check_en" is true, it will first run "check" method and then run "load" method.
# Optional: You can also use functions like numpy or scipy to help you check the correctness of DUT. You can use python class object to contain the inner values (optional).
# you can use binary (like 0b1011), hexadeciaml (like 0x1a) or normal number format in python for convenience. 
# please only generate the python codes, no other words.
# """%(STAGE5_SEQ_PYFORMAT)

# STAGE5_SEQ_TAIL = """
# def SignalTxt_to_dictlist(txt:str):
#     signals = []
#     lines = txt.strip().split("\\n")
#     for line in lines:
#         signal = {}
#         if line.startswith("[check]"):
#             signal["check_en"] = True
#             line = line[7:]
#         elif line.startswith("scenario"):
#             signal["check_en"] = False
#         else:
#             continue
#         line = line.strip().split(", ")
#         for item in line:
#             if "scenario" in item:
#                 item = item.split(": ")
#                 signal["scenario"] = item[1].replace(" ", "")
#             else:
#                 item = item.split(" = ")
#                 key = item[0]
#                 value = item[1]
#                 if "x" not in value and "z" not in value:
#                     signal[key] = int(value)
#                 else:
#                     if "x" in value:
#                         signal[key] = "x"
#                     else:
#                         signal[key] = "z"
#         signals.append(signal)
#     return signals
# with open("TBout.txt", "r") as f:
#     txt = f.read()
# vectors_in = SignalTxt_to_dictlist(txt)
# tb_pass = check_dut(vectors_in)
# print(tb_pass)
# """
# class Stage5_SEQ(BaseScriptStage):
#     """stage 5 (SEQ): generate the pychecker that receive the signals from testbench and check the correctness of DUT"""
#     def __init__(self, prob_data, response_stage1, response_stage3, **gptkwargs) -> None:
#         super().__init__("stage_5", **gptkwargs)
#         self.prob_data = prob_data
#         self.response_stage1 = response_stage1
#         self.response_stage3 = response_stage3 # currently not used
#         self.txt1 = STAGE5_SEQ_TXT1.replace(SIGNALTEMP_PLACEHOLDER_1, self.signal_dictlist_template(prob_data["header"], exclude_clk=True))
#         self.txt2 = STAGE5_SEQ_TXT2
#         self.pycode_tail = STAGE5_SEQ_TAIL

#     def make_prompt(self):
#         self.prompt = ""
#         # introduction
#         self.add_prompt_line(self.txt1)
#         # problem description
#         self.add_prompt_line("RTL circuit problem description:")
#         self.add_prompt_line(self.prob_data["description"])
#         # python rules
#         self.add_prompt_line("Here is the basic rules in python for the module. It is generated in previous stage. You can use it as a reference, but you should write your own python script. This is just for your better understanding:")
#         self.add_prompt_line(self.response_stage3)
#         # end
#         self.add_prompt_line(self.txt2)

#     def postprocessing(self):
#         # python codes
#         self.response = self.extract_code(self.response, "python")[-1]
#         self.Pychecker_code_out = self.response + self.pycode_tail

#     @staticmethod
#     def signal_dictlist_template(header:str, exclude_clk:bool=False) -> str:
#         """
#         for the automatic generation of signals in testbench
#         target: given the DUT header, generate the signal output template
#         eg: if we have a DUT header like "module DUT(input a, b, c, output d, e);", the signal output template should be like "[{"check_en": 0, "scenario": 1, "a": 1, "b": 0, "c":1, "d": 0, "e": 0}, {"check_en": 1, "scenario": 1, "a": 0, "b": 0, "c":1, "d": 0, "e": 0}]"
#         """
#         signals_dictlist1 = Stage5_SEQ.header_to_dictlist(header, exclude_clk=exclude_clk)
#         signals_dictlist2 = Stage5_SEQ.header_to_dictlist(header, exclude_clk=exclude_clk)
#         signals_dictlist3 = Stage5_SEQ.header_to_dictlist(header, check_en=True, exclude_clk=exclude_clk)
#         signals_dictlist = signals_dictlist1 + signals_dictlist2 + signals_dictlist3
        
#         return str(signals_dictlist)
    
#     @staticmethod
#     def header_to_dictlist(header:str, value=1, scenario_idx=1, check_en = False, exclude_clk:bool=False) -> str:
#         """
#         - header: the header of DUT
#         - template_scenario_idx: the scenario index in the template
#         - signal_value: the value of the signal in the template
#         - only: None: both input signal and output signal; "input": only input signal; "output": only output signal
#         - from header to signals in txt
#         - for the automatic generation of signals in testbench
#         - target: given the DUT header, generate the signal output template
#         - eg: if we have a DUT header like "module DUT(input clk, load, data, output q);", the signal output template should be like "$fdisplay(file, "scenario: %d, clk = %d, load = %d, data = %d, q = %d", scenario, clk, load, data, q);"
#         """
#         signals = utils.extract_signals(header)
#         if exclude_clk:
#             signals = [signal for signal in signals if signal["name"] not in ["clk", "clock"]]
#         dict_out = {}
#         dict_list_out = [dict_out]
#         dict_out["check_en"] = check_en
#         dict_out["scenario"] = scenario_idx
#         for signal in signals:
#             dict_out[signal["name"]] = value
#         return dict_list_out

class StageChecklist(BaseScriptStage):
    def __init__(self, TB_code:str, checklist_str:str, max_iter:int, **gptkwargs) -> None:
        super().__init__("stage_checklist", **gptkwargs)
        self.checklist = checklist_str # {"scenario 1": "xxx", "scenario 2": "xxx", ...}
        self.checklist_dict = json.loads(checklist_str)
        self.missing_scenarios = []
        self.max_iter = max_iter
        self.TB_code_out = TB_code
        self.exit = False
        self.iter = 0
        self.TB_modified = False

    def make_prompt(self):
        self.prompt = ""
        self.add_prompt_line("please check the if the testbench code contains all the items in the checklist:")
        self.add_prompt_line("testbench code here...\n")
        self.add_prompt_line(self.TB_code_out + "\n")
        self.add_prompt_line("please check the if the testbench code above contains all the scenarios in the checklist:")
        self.add_prompt_line(self.checklist)
        self.add_prompt_line("please reply 'YES' if all the items are included. If some of the items are missed in testbench, please add the missing items and reply the modified testbench code (full code).")
        self.add_prompt_line("HINT: the missing scenarios may be: " + str(self.missing_scenarios))
        self.add_prompt_line("VERY IMPORTANT: please ONLY reply 'YES' or the full code modified. NEVER remove other irrelevant codes!!!")
    
    def postprocessing(self):
        self.iter += 1
        if "YES" in self.response:
            self.exit = True
        else:
            self.TB_modified = True
            self.TB_code_out = self.extract_code(self.response, "verilog")[-1]

    def pre_check(self):
        """this function is called at the beginning of run() so that the stage can be skipped if needed"""
        self.missing_scenarios = []
        for key in self.checklist_dict.keys():
            if key.replace(" ", " = ") not in self.TB_code_out:
                self.missing_scenarios.append(key)

    def run(self):
        self.TB_modified = False
        while (not self.exit) and (self.iter < self.max_iter):
            self.pre_check()
            if self.missing_scenarios == []:
                self.exit = True
                self.conversation_message += "\n[SYSTEM PRECHECK] All scenarios are included in the testbench code. You can continue to the next stage."
            else:
                self.make_prompt()
                self.call_gpt()
                self.postprocessing()
