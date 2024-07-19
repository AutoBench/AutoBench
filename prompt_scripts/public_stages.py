"""
Description :   some public stages called by other scripts
Author      :   Ruidi Qiu (r.qiu@tum.de)
Time        :   2024/3/22 13:02:22
LastEdited  :   2024/4/28 15:03:45
"""

from .base_script import BaseScriptStage


STAGE1_TXT1="""1. Your task is to write a verilog testbench for an verilog RTL module code (we call it as "DUT", device under test). The infomation we have is the problem description that guides student to write the RTL code (DUT) and the header of the "DUT". Our target is to generate the verilog testbench for the DUT. This testbench can check if the DUT in verilog satisfies all technical requirements of the problem description.
2. You are in the first stage. In this stage, please summarize the technical details of the DUT and give me a technical specification of the testbench generation task, so we can use it to design its corresponding testbench.
3. The core of testbench is the testcases. It usually include two parts logically: the input signals to the DUT and the expected result signals from DUT. The testbench will send the input signals to DUT and check if the result signals are the same as the expected result signals. If they are the same, this means the DUT is passed. Otherwise the DUT fails.
4. Your technical specification should include these sections:
- section 1: specification of the DUT, including the module header of the RTL code. If table or other detailed data is provided in the original problem description, DO repeat them in your response. They are very important!!!
5. your response should be in the form of JSON.
6. below is the information including the problem description and the DUT header:"""
STAGE1_TXT2="""your response must be in JSON form. example:
{
  "circuit type": "...", # type: string. should be "CMB" for combinational circuit or "SEQ" for sequential circuit. you should only choose one from "CMB" and "SEQ".
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
2. you are in section 3; in this section, please give me the rules of an ideal DUT. you should give these rules in python. (For convenience, you can use binary or hexadecimal format in python, i.e. 0b0010 and 0x1a). Later we will use these ideal rules to generate expected values in each test scenario. currently you must only generate the rules. the input of these rules should be related to the test vectors from test scenario. the rule should give the expected values under test vectors. 
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
        self.checklist = checklist_str
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
        self.add_prompt_line("VERY IMPORTANT: please ONLY reply 'YES' or the full code modified. NEVER remove other irrelevant codes!!!")
    
    def postprocessing(self):
        self.iter += 1
        if "YES" in self.response:
            self.exit = True
        else:
            self.TB_modified = True
            self.TB_code_out = self.extract_code(self.response, "verilog")[-1]

    def run(self):
        self.TB_modified = False
        while (not self.exit) and (self.iter < self.max_iter):
            self.make_prompt()
            self.call_gpt()
            self.postprocessing()