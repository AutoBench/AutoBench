"""
Description :   The prompt script for pychecker's workflow on CMB circuits. The WF_pychecker_CMB script is only used in preliminary experiments. The final verion of pychecker is in WF_pychecker script, including a CMB/SEQ discriminator.
Author      :   AutoBench's Author (Anonymous Email)
Time        :   2024/3/22 10:40:43
LastEdited  :   2024/5/3 12:37:01
"""

from .base_script import BaseScript, BaseScriptStage
from . import public_stages
from .public_stages import StageChecklist

class WF_pychecker_CMB(BaseScript):
    """
    stages: stage1, stage2, stage3, stage3b, stage4
    check: check "scenario list"(stage2) in stage 4
    """
    def __init__(self, prob_data:dict, task_dir:str, config:object):
        super().__init__(prob_data, task_dir, config)
        self.max_check_iter = self.config.autoline.checklist.max
        self.py_code = ""

    def make_and_run_stages(self):
        # stage1
        self.stage1 = Stage1(self.prob_data, **self.gptkwargs)
        self.stage_operation(self.stage1)
        # stage2
        self.stage2 = Stage2(self.prob_data, self.stage1.response, **self.gptkwargs)
        self.stage_operation(self.stage2)
        # stage3
        self.stage3 = Stage3(self.prob_data, self.stage1.response, self.stage2.response, **self.gptkwargs)
        self.stage_operation(self.stage3)
        # stage4
        self.stage4 = Stage4(self.prob_data, self.stage1.response, self.stage2.response, **self.gptkwargs)
        self.stage_operation(self.stage4)
        # stagechecklist
        self.stagecheck = StageChecklist(self.TB_code, self.stage2.response, self.max_check_iter, **self.gptkwargs)
        self.stage_operation(self.stagecheck)
        # stage5
        self.stage5 = Stage5(self.prob_data, self.stage1.response, self.stage3.response, **self.gptkwargs)
        self.stage_operation(self.stage5)
        # self.TB_code += "\n" + stage3b.response   

    def make_and_run_reboot_stages(self, debug_dir):
        if self.reboot_mode == "TB":
            # stage4
            self.stage4 = Stage4(self.prob_data, self.stage1.response, self.stage2.response, **self.gptkwargs)
            self.stage_operation(self.stage4, debug_dir, reboot_en=True)
            # stagechecklist
            self.stagecheck = StageChecklist(self.TB_code, self.stage2.response, self.max_check_iter, **self.gptkwargs)
            self.stage_operation(self.stagecheck, debug_dir, reboot_en=True)
        elif self.reboot_mode == "PY":
            # stage5
            self.stage5 = Stage5(self.prob_data, self.stage1.response, self.stage3.response, **self.gptkwargs)
            self.stage_operation(self.stage5, debug_dir, reboot_en=True)
        else:
            raise ValueError("invalid reboot_mode in WF_pychecker script (circuit type: CMB)")

class Stage1(public_stages.Stage1):
    """
    stage1 for pychecker, the same as RTLchecker0306.Stage1
    """
    def __init__(self, prob_data:dict, **gptkwargs):
        super().__init__(prob_data, **gptkwargs)

class Stage2(public_stages.Stage2):
    """
    stage2 for pychecker, the same as RTLchecker0306.Stage2
    """
    def __init__(self, prob_data:dict, response_stage1:str, **gptkwargs):
        super().__init__(prob_data, response_stage1, **gptkwargs)

class Stage3(public_stages.Stage3):
    """
    stage3 for pychecker, the same as RTLchecker0306.Stage3
    """
    def __init__(self, prob_data:dict, response_stage1:str, response_stage2:str, **gptkwargs):
        super().__init__(prob_data, response_stage1, response_stage2, **gptkwargs)

SIGNALTEMP_PLACEHOLDER_1 = "/* SIGNAL TEMPLATE 1 */"
SIGNALTEMP_PLACEHOLDER_1A = "/* SIGNAL TEMPLATE 1A */"
SIGNALTEMP_PLACEHOLDER_1B = "/* SIGNAL TEMPLATE 1B */"

STAGE4_TXT1 = """
1. Your task is to write a verilog testbench for an verilog RTL module code (we call it as "DUT", device under test). The infomation we have is 
- 1.1. the problem description that guides student to write the RTL code (DUT) and the header of the "DUT". 
- 1.2. the module header.
- 1.3. the technical specification of testbench
- 1.4. test scenarios which determines value and sequential information of test vectors

2. you are in section 4. in this section, our target is to generate the verilog testbench for the DUT. This testbench can export the input and output signals of DUT at the important time points. The exported data will be send to a python script to check the correctness of DUT. 
ATTENTION: The testbench does not need to check the DUT's output but only export the signals of DUT.
Instruction of saving signals to file: 
(1) you should use $fopen and $fdisplay to export the important signals in testbench. the file name is "TBout.txt".
(2) When running testbench, for one time point, you should export 1 line. the example of the printed line is "%s"; If one scenario has multiple test cases, use letter suffix to represent different test cases, like "%s", "%s".
(3) Attention: before $fdisplay, you should always have a delay statement to make sure the signals are stable.
(4) the signals you save is the input and output of DUT, you should determine the signals according to DUT's header:
"""%(SIGNALTEMP_PLACEHOLDER_1, SIGNALTEMP_PLACEHOLDER_1A, SIGNALTEMP_PLACEHOLDER_1B)

STAGE4_TXT2 = """
The testbench does not need to check the DUT's output but only export the signals of DUT.
Instruction of saving signals to file: 
(1) you should use $fopen and $fdisplay to export the important signals in testbench. the file name is "TBout.txt". 
(2) When running testbench, for one time point, you should export 1 line. the example of the printed line is "%s"; If one scenario has multiple test cases, use letter suffix to represent different test cases, like "%s", "%s".
(3) Attention: before $fdisplay, you should always have a delay statement to make sure the signals are stable.
(4) the signals you save is the input and output of DUT, you should determine the signals according to DUT's header.
please only generate the verilog codes, no other words.
"""%(SIGNALTEMP_PLACEHOLDER_1, SIGNALTEMP_PLACEHOLDER_1A, SIGNALTEMP_PLACEHOLDER_1B)

class Stage4(BaseScriptStage):
    """stage 4: generate the testbench that export the signals of DUT to a file"""
    def __init__(self, prob_data, response_stage1, response_stage2, **gptkwargs) -> None:
        super().__init__("stage_4", **gptkwargs)
        self.prob_data = prob_data
        self.response_stage1 = response_stage1
        self.response_stage2 = response_stage2
        self.txt1 = STAGE4_TXT1
        self.txt2 = STAGE4_TXT2
        self.txt1 = self.txt1.replace(SIGNALTEMP_PLACEHOLDER_1, header_to_SignalTxt_template(prob_data["header"], signal_value=r"%d"))
        self.txt1 = self.txt1.replace(SIGNALTEMP_PLACEHOLDER_1A, header_to_SignalTxt_template(prob_data["header"], "1a", signal_value=r"%d"))
        self.txt1 = self.txt1.replace(SIGNALTEMP_PLACEHOLDER_1B, header_to_SignalTxt_template(prob_data["header"], "1b", signal_value=r"%d"))
        self.txt2 = self.txt2.replace(SIGNALTEMP_PLACEHOLDER_1, header_to_SignalTxt_template(prob_data["header"], signal_value=r"%d"))
        self.txt2 = self.txt2.replace(SIGNALTEMP_PLACEHOLDER_1A, header_to_SignalTxt_template(prob_data["header"], "1a", signal_value=r"%d"))
        self.txt2 = self.txt2.replace(SIGNALTEMP_PLACEHOLDER_1B, header_to_SignalTxt_template(prob_data["header"], "1b", signal_value=r"%d"))

    def make_prompt(self):
        self.prompt = ""
        self.add_prompt_line(self.txt1)
        # DUT header
        self.add_prompt_line(self.prob_data["header"])
        # other information:
        self.add_prompt_line("Your other information:")
        # problem description
        self.add_prompt_line("RTL circuit problem description:")
        self.add_prompt_line(self.prob_data["description"])
        # specification
        self.add_prompt_line("RTL testbench specification:")
        self.add_prompt_line(self.response_stage1)
        # rules
        self.add_prompt_line("IMPORTANT - test scenario:")
        self.add_prompt_line(self.response_stage2)
        # end
        self.add_prompt_line(self.txt2)

    def postprocessing(self):
        # verilog codes
        self.response = self.extract_code(self.response, "verilog")[-1]
        self.TB_code_out = self.response

STAGEPYGEN_PYFORMAT = """Your python scritp should contain a function "check_dut", its header is "def check_dut(test_vectors:list) -> bool:". It can also call other functions you write in this script. If all test scenarios passed, function "check_dut" should return an empty list [], otherwise it should return the list of failed scenarios indexes. You can use binary (like 0x1101), hexadecimal (like 0x1a) or normal number format in python.""" # TODO: later this function will also show the failed scenario idx

STAGEPYGEN_TXT1 = """
1. background: Your task is to verify the functional correctness of a verilog RTL module code (we call it as "DUT", device under test). Our plan is to first export the signals (input and output) of the DUT under test scenarios. Then, we will use a python script to check the correctness of DUT.
2. You are in the last stage. In this stage, we already export the signals of DUT. Your task is to write a python script. The python script contains one main function "check_dut" and other functions to be called by "check_dut" (this is optional). The input of "check_dut" is the signals of DUT in the format below: (the signal names are real, but the values are just for example)
%s
The main function "check_dut" should check the correctness according to the input signals. The input signals are all in decimal format. It will be called by other codes later.
3. %s 
4. You have the information below to help you check the correctness of DUT:
"""%(SIGNALTEMP_PLACEHOLDER_1, STAGEPYGEN_PYFORMAT)

STAGEPYGEN_TXT2 = """
[IMPORTANT] %s
Optional: You can also use functions from numpy and scipy to help you check the correctness of DUT.
you can use binary (like 0b1011), hexadeciaml (like 0x1a) or normal number format in python for convenience. 
please only generate the python codes, no other words.
"""%(STAGEPYGEN_PYFORMAT)

STAGEPYGEN_TAIL = """
def SignalTxt_to_dictlist(txt:str):
    lines = txt.strip().split("\\n")
    signals = []
    for line in lines:
        signal = {}
        line = line.strip().split(", ")
        for item in line:
            if "scenario" in item:
                item = item.split(": ")
                signal["scenario"] = item[1]
            else:
                item = item.split(" = ")
                key = item[0]
                value = item[1]
                if "x" not in value and "z" not in value:
                    signal[key] = int(value)
                else:
                    signal[key] = value 
        signals.append(signal)
    return signals
with open("TBout.txt", "r") as f:
    txt = f.read()
vectors_in = SignalTxt_to_dictlist(txt)
tb_pass = check_dut(vectors_in)
print(tb_pass)
"""
class Stage5(BaseScriptStage):
    """stage 5: generate the pychecker that receive the signals from testbench and check the correctness of DUT"""
    def __init__(self, prob_data, response_stage1, response_stage3, **gptkwargs) -> None:
        super().__init__("stage_5", **gptkwargs)
        self.prob_data = prob_data
        self.response_stage1 = response_stage1
        self.response_stage3 = response_stage3 # currently not used
        self.txt1 = STAGEPYGEN_TXT1.replace(SIGNALTEMP_PLACEHOLDER_1, self.signal_dictlist_template(prob_data["header"]))
        self.txt2 = STAGEPYGEN_TXT2
        self.pycode_tail = STAGEPYGEN_TAIL

    def make_prompt(self):
        self.prompt = ""
        # introduction
        self.add_prompt_line(self.txt1)
        # problem description
        self.add_prompt_line("RTL circuit problem description:")
        self.add_prompt_line(self.prob_data["description"])
        # specification
        self.add_prompt_line("Checker specification:")
        self.add_prompt_line(self.response_stage1)
        # python rules (optional)
        self.add_prompt_line("Here is the basic rules in python for the module. It is generated in previous stage. You can use it as a reference, but you should write your own python script. This is just for your better understanding:")
        self.add_prompt_line(self.response_stage3)
        # end
        self.add_prompt_line(self.txt2)

    def postprocessing(self):
        # python codes
        self.response = self.extract_code(self.response, "python")[-1]
        self.Pychecker_code_out = self.response + self.pycode_tail

    @staticmethod
    def signal_dictlist_template(header:str) -> str:
        """
        for the automatic generation of signals in testbench
        target: given the DUT header, generate the signal output template
        eg: if we have a DUT header like "module DUT(input a, b, c, output d, e);", the signal output template should be like "[{"scenario": "1", "a": 1, "b": 0, "c":1, "d": 0, "e": 0}, {"scenario": "2", "a": 0, "b": 0, "c":1, "d": 0, "e": 0}]"
        """
        signals1 = header_to_SignalTxt_template(header, "1")
        signals2 = header_to_SignalTxt_template(header, "2")
        signals_dictlist1 = SignalTxt_to_dictlist(signals1)
        signals_dictlist2 = SignalTxt_to_dictlist(signals2)
        signals_dictlist = signals_dictlist1 + signals_dictlist2
        return str(signals_dictlist)

    
def header_to_SignalTxt_template(header:str, template_scenario_idx:str="1", signal_value:str="0"):
    """
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

def SignalTxt_to_dictlist(txt:str) -> list:
    """
    - from txt to list of dicts
    - this function is used to extract signals and scenario information from a out.txt file. 
    - the TBout.txt file is generated by testbench, which is in the pychecker workflow
    - the format of each line in TBout.txt is like:
    - "scenario: x, a = x, b = x, c = x, d = x, e = x"
    - we want: [{"scenario": x, "a": x, ...}, {...}]
    """
    lines = txt.strip().split("\n")
    signals = []
    for line in lines:
        signal = {}
        line = line.strip().split(", ")
        for item in line:
            if "scenario" in item:
                item = item.split(": ")
                signal["scenario"] = item[1]
            else:
                item = item.split(" = ")
                key = item[0]
                value = item[1]
                if "x" not in value and "z" not in value:
                    signal[key] = int(value)
                else:
                    signal[key] = value 
        signals.append(signal)
    return signals