"""
Description :   The prompt script for pychecker workflow
Author      :   Ruidi Qiu (r.qiu@tum.de)
Time        :   2024/3/22 10:40:43
LastEdited  :   2024/5/3 22:55:30
"""

import json
from . import utils
from .base_script import BaseScript, BaseScriptStage
from .script_pychecker_CMB import Stage4 as Stage4_CMB, Stage5 as Stage5_CMB
from .script_pychecker_SEQ import Stage4_SEQ, Stage4b_SEQ, Stage5_SEQ
from .public_stages import StageChecklist as StageChecklist_old

class WF_pychecker(BaseScript):
    """
    stages: stage1, stage2, stage3, stage3b, stage4
    check: check "scenario list"(stage2) in stage 4
    """
    def __init__(self, prob_data:dict, task_dir:str, config:object):
        super().__init__(prob_data, task_dir, config)
        self.max_check_iter = self.config.autoline.checklist.max

    def make_and_run_stages(self):
        # stage0
        self.stage0 = Stage0(self.prob_data, **self.gptkwargs)
        self.stage_operation(self.stage0)
        self.circuit_type = self.stage0.circuit_type
        # stage1
        self.stage1 = Stage1(self.prob_data, **self.gptkwargs)
        self.stage_operation(self.stage1)
        # stage2
        self.stage2 = Stage2(self.prob_data, self.stage1.response, **self.gptkwargs)
        self.stage_operation(self.stage2)
        # stage3
        self.stage3 = Stage3(self.prob_data, self.stage1.response, self.stage2.response, **self.gptkwargs)
        self.stage_operation(self.stage3)
        # split into CMB and SEQ
        if self.circuit_type == "CMB":
            self.make_and_run_stages_CMB()
        else:
            self.make_and_run_stages_SEQ()

    def make_and_run_stages_CMB(self):
        # stage4
        self.stage4 = Stage4_CMB(self.prob_data, self.stage1.response, self.stage2.response, **self.gptkwargs)
        self.stage_operation(self.stage4)
        # stagechecklist
        self.stagecheck = StageChecklist_old(self.TB_code, self.stage2.response, self.max_check_iter, **self.gptkwargs)
        self.stage_operation(self.stagecheck)
        # we perform pychecker_CMB_TB_standardization after stagechecklist because there is no stage 4b
        # self.TB_code = utils.pychecker_CMB_TB_standardization(self.TB_code, self.prob_data["header"])
        # stage5
        self.stage5 = Stage5_CMB(self.prob_data, self.stage1.response, self.stage3.response, **self.gptkwargs)
        self.stage_operation(self.stage5)

    def make_and_run_stages_SEQ(self):
        self.py_debug_focus = True # extract core part of the code when debugging. CMB does not need this because CMB's result is already good and time is limited. But this would be easy to do in the future.
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
        if self.circuit_type == "CMB":
            self.make_and_run_reboot_stages_CMB(debug_dir)
        else:
            self.make_and_run_reboot_stages_SEQ(debug_dir)
        
    def make_and_run_reboot_stages_CMB(self, debug_dir):
        if self.reboot_mode == "TB":
            # stage4
            self.stage4 = Stage4_CMB(self.prob_data, self.stage1.response, self.stage2.response, **self.gptkwargs)
            self.stage_operation(self.stage4, debug_dir, reboot_en=True)
            # stagechecklist
            self.stagecheck = StageChecklist_old(self.TB_code, self.stage2.response, self.max_check_iter, **self.gptkwargs)
            self.stage_operation(self.stagecheck, debug_dir, reboot_en=True)
            # pychecker_CMB_TB_standardization
            # self.TB_code = utils.pychecker_CMB_TB_standardization(self.TB_code, self.prob_data["header"])
        elif self.reboot_mode == "PY":
            # stage5
            self.stage5 = Stage5_CMB(self.prob_data, self.stage1.response, self.stage3.response, **self.gptkwargs)
            self.stage_operation(self.stage5, debug_dir, reboot_en=True)
        else:
            raise ValueError("invalid reboot_mode in WF_pychecker script (circuit type: CMB)")

    def make_and_run_reboot_stages_SEQ(self, debug_dir):
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



SIGNALTEMP_PLACEHOLDER_1 = "/* SIGNAL TEMPLATE 1 */"
SIGNALTEMP_PLACEHOLDER_1A = "/* SIGNAL TEMPLATE 1A */"
SIGNALTEMP_PLACEHOLDER_1B = "/* SIGNAL TEMPLATE 1B */"


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
        self.add_prompt_line("please only reply verilog codes. reply_format:\n```verilog\nyour_code_here...\n```")

    def postprocessing(self):
        self.response = self.extract_code(self.response, "verilog")[-1]
        self.circuit_type = utils.circuit_type_by_code(self.response)

STAGE1_TXT1="""1. Your task is to write a verilog testbench for an verilog RTL module code (we call it as "DUT", device under test). The infomation we have is the problem description that guides student to write the RTL code (DUT) and the header of the "DUT". Our target is to generate the verilog testbench for the DUT. This testbench can check if the DUT in verilog satisfies all technical requirements of the problem description.
2. You are in the first stage. In this stage, please summarize the technical details of the DUT and give me a technical specification of the testbench generation task, so we can use it to design its corresponding testbench.
3. The core of testbench is the testcases. It usually include two parts logically: the input signals to the DUT and the expected result signals from DUT. The testbench will send the input signals to DUT and check if the result signals are the same as the expected result signals. If they are the same, this means the DUT is passed. Otherwise the DUT fails.
4. Your technical specification should include these sections:
- section 1: specification of the DUT, including the module header of the RTL code. If table or other detailed data is provided in the original problem description, DO repeat them in your response. They are very important!!!
5. your response should be in the form of JSON.
6. below is the information including the problem description and the DUT header:"""
STAGE1_TXT2="""your response must be in JSON form. example:
{
  "important data": "...", # type: string. If no table, state transition or other direct data, leave this with ""
  "technical specifications": ["...", "...", ...] # each element of the list is one specification string, the starting of the string is its index 
}
"""
class Stage1(BaseScriptStage):
    def __init__(self, prob_data, **gptkwargs):
        gptkwargs["json_mode"] = True
        super().__init__("stage_1", **gptkwargs)
        self.prob_data = prob_data
        self.txt1 = STAGE1_TXT1
        self.txt2 = STAGE1_TXT2
    
    def make_prompt(self):
        self.prompt = ""
        self.add_prompt_line(self.txt1)
        # problem description
        self.add_prompt_line("RTL circuit problem description:")
        self.add_prompt_line(self.prob_data["description"])
        # DUT header
        self.add_prompt_line("DUT header:")
        self.add_prompt_line(self.prob_data["header"])
        # template
        self.add_prompt_line(self.txt2)

    # def postprocessing(self):
    #     self.spec_dict = json.loads(self.response)


STAGE2_TXT1="""1. Your task is to write a verilog testbench for an verilog RTL module code (we call it as "DUT", device under test). The infomation we have is the problem description that guides student to write the RTL code (DUT) and the header of the "DUT". Our target is to generate the verilog testbench for the DUT. This testbench can check if the DUT in verilog satisfies all technical requirements of the problem description.
2. you are in section 2. in this section, please give me the test scenarios. you only need to describe the stimulus in each test scenarios. If time is important, please inform the clock cycle information. we will use the stimulus description to generate the test vectors and send them to DUT. you must not tell the expected results even though you know that. 
3. your information is:"""
STAGE2_TXT2="""
you only need to describe the stimulus in each test scenarios. If time is important, please inform the clock cycle information. we will use the stimulus description to generate the test vectors and send them to DUT. you must not tell the expected results even though you know that. 

your response must be in JSON form. example:
{
  "scenario 1": "...", # each content is a string
  "scenario 2": "...",
  "scenario 3": "...",
  ...
}"""
class Stage2(BaseScriptStage):
    def __init__(self, prob_data, response_stage1, **gptkwargs) -> None:
        gptkwargs["json_mode"] = True
        super().__init__("stage_2", **gptkwargs)
        self.prob_data = prob_data
        self.response_stage1 = response_stage1
        self.txt1 = STAGE2_TXT1
        self.txt2 = STAGE2_TXT2

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
        # template
        self.add_prompt_line(self.txt2)

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

# more stages see script_pychecker_CMB and script_pychecker_SEQ