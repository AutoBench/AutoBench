"""
Description :   the base script for prompt scripts
Author      :   AutoBench's Author (Anonymous Email)
Time        :   2024/3/22 10:59:34
LastEdited  :   2024/4/30 20:31:02
"""

from LLM_call import llm_call, extract_code, message_to_conversation
from utils.utils import Timer, get_time
import os
import loader_saver as ls
import copy

DEFAULT_SYSMESSAGE = "You are the strongest AI in the world. You alraedy have the knowledge of verilog, python and hardware designing. Do not save words by discarding information. I will tip you 200$ if you can fullfill the tasks I give you."

IDENTIFIER = {
    "tb_start" : "```verilog",
    "tb_end" : "```"
}

TESTBENCH_TEMPLATE = """%s
`timescale 1ns / 1ps
(more verilog testbench code here...)
endmodule
%s""" % (IDENTIFIER["tb_start"], IDENTIFIER["tb_end"])

__all__ = ["BaseScriptStage", "BaseScript"]

class BaseScriptStage:
    """
    - the base stage for prompt scripts
    - the functions that triggered when running:
        - make_prompt: make the prompt for gpt (must be implemented)
        - call_gpt: call gpt
        - postprocessing: postprocessing the response (default is empty)
    - gptkwargs: the kwargs for llm_call
        - gpt_model: the model name
        - api_key_path: the path of gpt key
        - sysmessage: (can be ignored) the system message 
        - json_mode: (can be ignored) the json mode
        - temperature: (can be ignored) the temperature
    """
    def __init__(self, stage_name, **gptkwargs) -> None:
        self.stage_name = stage_name
        self.gpt_model = gptkwargs["gpt_model"] 
        self.api_key_path = gptkwargs["api_key_path"]
        self.system_message = gptkwargs.get("system_message", DEFAULT_SYSMESSAGE)
        self.json_mode = gptkwargs.get("json_mode", None)
        self.temperature = gptkwargs.get("temperature", None)
        self.time = 0.0
        self.prompt = ""
        self.response = ""
        self.print_message = ""
        self.gptinfo = {}
        self.conversation_message = ""
        self.conversation_file_suffix = ".txt"
        self.reboot = False
        self.circuit_type = None # "CMB" or "SEQ"; pychecker will use this; you should set it in make_and_run_stages;
        
    @property
    def will_gen_TB(self):
        if hasattr(self, "TB_code_out"):
            return True
        else:
            return False
        
    @property
    def will_gen_Pychecker(self):
        if hasattr(self, "Pychecker_code_out"):
            return True
        else:
            return False

    def __call__(self, *args, **kwargs):
        with Timer(print_en=False) as t:
            self.run(*args, **kwargs)
        self.time = t.interval
        self.record()
        pass    

    def run(self):
        self.make_prompt()
        self.call_gpt()
        self.postprocessing()

    def make_prompt(self):
        raise NotImplementedError

    def call_gpt(self):
        """
        actually it should be call_llm, but I dont want to modify the old code
        """
        gpt_messages = [{"role": "user", "content": self.prompt}]
        other_kwargs = {}
        if self.temperature is not None:
            other_kwargs["temperature"] = self.temperature
        if self.json_mode is not None:
            other_kwargs["json_mode"] = self.json_mode
        self.response, self.gptinfo = llm_call(input_messages=gpt_messages, model=self.gpt_model, api_key_path=self.api_key_path, system_message=self.system_message, **other_kwargs)
        self.conversation_message += message_to_conversation(self.gptinfo["messages"])

    def postprocessing(self):
        """empty function"""
        pass

    def record(self):
        self.print_message = "%s ends (%.2fs used, time: %s)" % (self.stage_name, self.time, get_time())
        print(self.print_message)
        
    # tools
    def save_log(self, config:object):
        ls.save_log_line(self.print_message, config)

    def save_conversation(self, save_dir:str):
        """This function will save the conversation to a file in save_dir. It will be called in stage_operation of BaseScript"""
        if save_dir.endswith("/"):
            save_dir = save_dir[:-1]
        file_name = self.stage_name + self.conversation_file_suffix
        path = os.path.join(save_dir, file_name)
        with open(path, "w") as f:
            f.write(self.conversation_message)

    # def reboot(self):
    #     self.reboot_en = True
    #     self.conversation_message = ""
    #     self.time = 0.0
    #     self.prompt = ""
    #     self.response = ""
    #     self.print_message = ""
    #     self.gptinfo = {}
    #     self.conversation_message = ""
    #     self.conversation_file_suffix = ".txt"
    #     # TODO in your script, you should also reset the custom attributes

    def extract_code(self, text, code_type):
        """
            #### function:
            - extract code from text
            #### input:
            - text: str, gpt's response
            - code_type: str, like "verilog"
            #### output:
            - list of found code blocks
        """
        return extract_code(text=text, code_type=code_type)
    
    def update_tokens(self, tokens):
        tokens["prompt"] += self.gptinfo.get("usage", {}).get("prompt_tokens", 0) # in case gpt has not been called
        tokens["completion"] += self.gptinfo.get("usage", {}).get("completion_tokens", 0)
        return tokens

    def add_prompt_line(self, prompt):
        self.prompt += prompt + "\n"

class BaseScript:
    """
    the base class for prompt scripts
    - the functions that triggered when running:
        - make_and_run_stages: make and run stages (must be implemented)
        - postprocessing: postprocessing the response (default is empty)
        - save_codes: save the generated codes
    """
    def __init__(self, prob_data:dict, task_dir:str, config:object) -> None:
        self.stages = []
        self.task_dir = task_dir if not task_dir.endswith("/") else task_dir[:-1]
        self.config = config
        self.gptkwargs = {
            "gpt_model": self.config.gpt.model,
            "api_key_path": self.config.gpt.key_path
        }
        self.prob_data = prob_data
        self.TB_code = ""
        self.TB_code_dir = os.path.join(self.task_dir, "TBgen_codes") # pychecker codes will be saved in the same directory
        self.TB_code_name = prob_data["task_id"] + "_tb.v"
        self.Pychecker_code = "" # only for pychecker scripts
        self.Pychecker_code_name = prob_data["task_id"] + "_tb.py"
        self.empty_DUT_name = prob_data["task_id"] + ".v"
        self.empty_DUT = prob_data["header"] + "\n\nendmodule\n"
        self.stages_gencode = [] # includes all the stages that generate code, will be used in rebooting generation; see more in stage operation
        self.tokens = {"prompt": 0, "completion": 0}
        self.time = 0.0
        self.reboot_idx = -1 # start from 0; -1 means no reboot. the reboot index will be increased by 1 after each reboot
        self.reboot_stages = [] #[reboot_stages_iter_0, reboot_stages_iter_1, ...]
        self.reboot_mode = "TB" # "TB" or "PY"; modified by run_reboot; checked in make_and_run_reboot_stages if needed
        self.py_debug_focus = False # if True, when debug python, will only send the upper part (no check_dut); specific for pychecker
        self.checklist_worked = False # if True, the scenario checklist did help our work. This is a flag for further analysis
        os.makedirs(self.TB_code_dir, exist_ok=True)

    @property
    def Pychecker_en(self):
        if self.Pychecker_code != "":
            return True
        else:
            return False
    
    @property
    def Pychecker_code_dir(self):
        return self.TB_code_dir

    def __call__(self, *args, **kwargs):
        self.run(*args, **kwargs)

    def run(self):
        self.make_and_run_stages()
        self.compute_time_tokens()
        self.postprocessing()
        self.save_codes()

    def make_and_run_stages(self):
        """
        - in this function, you should make stages and run them
        - for example:
        ::

            stage1 = Stage1(**kwargs)
            self.stage_operation(stage1)
        """
        raise NotImplementedError("No make_and_run_stages: You should implement this function in your own script")
    
    def make_and_run_reboot_stages(self, debug_dir):
        raise NotImplementedError("No reboot settings: You should implement this function in your own script")

    def postprocessing(self):
        """empty function"""
        pass

    def save_codes(self, codes_dir:str=None):
        if codes_dir is None:
            codes_dir = self.TB_code_dir
        os.makedirs(codes_dir, exist_ok=True)
        TB_code_path = os.path.join(codes_dir, self.TB_code_name)
        with open(TB_code_path, "w") as f:
            f.write(self.TB_code)
        empty_DUT_path = os.path.join(codes_dir, self.empty_DUT_name)
        with open(empty_DUT_path, "w") as f:
            f.write(self.empty_DUT)
        # save pychecker code if have
        if self.Pychecker_en:
            Pychecker_code_path = os.path.join(codes_dir, self.Pychecker_code_name)
            with open(Pychecker_code_path, "w") as f:
                f.write(self.Pychecker_code)
    
    def stage_operation(self, stage:BaseScriptStage, conversation_dir:str=None, reboot_en:bool=False):
        """
        - what to do on a stage after making it; will be called in make_and_run_stages
        - run, save stages and renew the generated codes of current wf
        """
        if conversation_dir is None:
            conversation_dir = self.task_dir
        stage()
        if reboot_en:
            self.reboot_stages[self.reboot_idx].append(stage)
        else:
            self.stages.append(stage)
        stage.save_conversation(conversation_dir)
        stage.save_log(self.config)
        if stage.will_gen_TB:
            self.TB_code = stage.TB_code_out
        if stage.will_gen_Pychecker:
            self.Pychecker_code = stage.Pychecker_code_out
        # for checklist:
        if hasattr(stage, "TB_modified"): # this attr is in checklist_stage
            self.checklist_worked = stage.TB_modified
        # will automaticly add stages to self.stages_gencode
        # the rule is: this stage will generate TB or its previous stage is in self.stages_gencode; also, this stage is not reboot stage
        # if (stage.will_gen_TB or (len(self.stages_gencode) > 0 and self.stages_gencode[-1] in self.stages)) and not stage.reboot_en:
        #     self.stages_gencode.append(stage)

    def run_reboot(self, debug_dir, reboot_mode="TB"):
        """
        - regenerate the TB code
        """
        self.reboot_idx += 1
        self.reboot_stages.append([])
        self.TB_code = ""
        self.reboot_mode = reboot_mode # this will be checked in make_and_run_reboot_stages if needed
        debug_dir = debug_dir[:-1] if debug_dir.endswith("/") else debug_dir
        # will be discarded by 28/04/2024
        # make and run stages
        # for stage in self.stages_gencode:
        #     new_stage = copy.deepcopy(stage)
        #     new_stage.stage_name = stage.stage_name + "_reboot" + str(self.reboot_idx)
        #     # new_stage.reboot()
        #     new_stage.reboot_en = True
        #     self.stage_operation(new_stage, debug_dir)
        #     reboot_stages_in_this_iter.append(new_stage)
        self.make_and_run_reboot_stages(debug_dir)
        # postprocessing
        self.compute_time_tokens(self.reboot_stages[self.reboot_idx])
        self.postprocessing()
        # save codes
        self.save_codes(debug_dir)

    def clear_time_tokens(self):
        self.time = 0.0
        self.tokens = {"prompt": 0, "completion": 0}

    def compute_time_tokens(self, stages=None):
        if stages is None:
            stages = self.stages
        for stage in stages:
            self.time += stage.time
            self.tokens = stage.update_tokens(self.tokens)

    def save_log(self, line):
        ls.save_log_line(line, self.config)

    def __call__(self, *args, **kwargs):
        self.run(*args, **kwargs)
        pass
