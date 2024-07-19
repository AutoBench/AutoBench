"""
Description :   "directgen" script for prompt scripts
Author      :   Ruidi Qiu (r.qiu@tum.de)
Time        :   2024/3/30 17:40:38
LastEdited  :   2024/5/1 17:44:05
"""

from .base_script import BaseScript, BaseScriptStage, TESTBENCH_TEMPLATE

class WF_directgen(BaseScript):
    """
    stages: stage1
    """
    def __init__(self, prob_data:dict, task_dir:str, config:object):
        super().__init__(prob_data, task_dir, config)

    def make_and_run_stages(self):
        # stage1
        stage1 = Stage1(self.prob_data, **self.gptkwargs)
        self.stage_operation(stage1)

    def make_and_run_reboot_stages(self, debug_dir):
        # stage1
        stage1 = Stage1(self.prob_data, **self.gptkwargs)
        self.stage_operation(stage1, debug_dir, reboot_en=True)

STAGE1_TXT1 = """
Your task is to write a verilog testbench for an verilog RTL module code (we call it as "DUT", device under test). The infomation we have is the problem description that guides student to write the RTL code (DUT) and the header of the "DUT".
"""
STAGE1_TXT2 = """
very very IMPORTANT: If all the test cases pass, the testbench should display "all test cases passed". If any one of the test cases fails, testbench should not display "all test caess passed". DO NOT generate any .vcd file.
please don't reply other words except the testbench codes.
"""
class Stage1(BaseScriptStage):
    def __init__(self, prob_data, **gptkwargs) -> None:
        super().__init__("stage_1", **gptkwargs)
        self.prob_data = prob_data
        self.txt1 = STAGE1_TXT1
        self.txt2 = STAGE1_TXT2
        self.TB_code_out = ""

    def make_prompt(self):
        self.prompt = ""
        self.add_prompt_line(self.txt1)
        # testbench template
        self.add_prompt_line("your testbench template is:")
        self.add_prompt_line(TESTBENCH_TEMPLATE)
        # problem description
        self.add_prompt_line("problem description:")
        self.add_prompt_line(self.prob_data["description"])
        # DUT header
        self.add_prompt_line("DUT header:")
        self.add_prompt_line(self.prob_data["header"])
        # end
        self.add_prompt_line(self.txt2)

    def postprocessing(self):
        # verilog codes
        self.response = self.extract_code(self.response, "verilog")[-1]
        self.TB_code_out = self.response