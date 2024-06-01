"""
Description :   Automatic pipeline of Chatbench: from HDLBits problem to simulation
Author      :   AutoBench's Author (Anonymous Email)
Time        :   2023/12/7 15:13:00
LastEdited  :   2024/5/3 17:17:07
autoline.py (c) 2023
"""

from loader_saver import load_json_dict, save_dict_json_form, load_txt, print_and_save
from data.probset import HDLBitsProbset
import loader_saver as ls
import LLM_call as gpt
import iverilog_call as iv
import python_call as py
import analyze as al
import json
import sys
from utils.utils import Timer, get_time
import os
from copy import deepcopy
from prompt_scripts import get_script, BaseScript

TC_PASS_CHECK_LIST_TB_GEN = ["All test cases passed", "all test cases passed", "All Test Cases Passed"]
TC_PASS_CHECK_LIST_TB_GOLDEN = ['Mismatches: 0 in ', 'Hint: Total mismatched samples is 0 out of']
TC_PASS_CHECK_LIST_PYCHECKER = ["[]"]

IDENTIFIER = {
    "tb_start" : "```verilog",
    "tb_end" : "```"
}

TESTBENCH_TEMPLATE = """%s
`timescale 1ns / 1ps
(more verilog testbench code here...)
endmodule
%s""" % (IDENTIFIER["tb_start"], IDENTIFIER["tb_end"])

DEBUG_TEMPLATE = """please fix the verilog testbench code below according to the error message below. please directly give me the corrected verilog testbench codes.
Attention: never remove the irrelevant codes!!!
your verilog testbench should be like:
%s
please only reply the full code modified. NEVER remove other irrelevant codes!!!
The testbench I give you is the one with error. To be convienient, each of the line begins with a line number. The line number also appears at the error message. You should use the line number to locate the error with the help of error message.
""" % (TESTBENCH_TEMPLATE)

DEBUG_TEMPLATE_PY = """please fix the python code below according to the error message below. please directly give me the corrected verilog testbench codes.
Attention: never remove the irrelevant codes!!!
please only reply the full code modified. NEVER remove other irrelevant codes!!!
The python code I give you is the one with error. To be convienient, each of the line begins with a line number. The line number also appears at the error message. You should use the line number to locate the error with the help of error message.
"""

DEBUG_TEMPLATE_END = """
VERY IMPORTANT: please ONLY reply the full code modified. NEVER remove other irrelevant codes!!!
Your testbench SHOULD NOT have the line number at the beginning of each line!!!
"""

TB_CODE_SUBDIR = "TBgen_codes/"

def run_autoline(config):
    """
    - this is the main function of autoline
    - support two kinds of pipeline:
        - pipeline_one_prob: pipeline for one problem
        - pipeline_all_prob: pipeline for all problems (TODO)
    """
    # stage_template_path = config.load.stage_template.path
    # stage_template_data = load_stage_template(stage_template_path)
    TBgen_prompt_script = config.autoline.promptscript
    cfg_probset = config.autoline.probset
    probset_paras = {
        "path": cfg_probset.path,
        "more_info_paths": cfg_probset.more_info_paths,
        "only_tasks": cfg_probset.only,
        "exclude_tasks": cfg_probset.exclude,
        "filter_content": cfg_probset.filter[0]
    }
    probset_paras["more_info_paths"].append(cfg_probset.mutant_path)
    if cfg_probset.gptgenRTL_path is not None:
        probset_paras["more_info_paths"].append(cfg_probset.gptgenRTL_path)
    probset = HDLBitsProbset(**probset_paras)
    if cfg_probset.exclude_json is not None:
        if type(cfg_probset.exclude_json) == str:
            exclude_tasks = HDLBitsProbset()
            exclude_tasks.data = ls.load_json_dict(cfg_probset.exclude_json)
            exclude_task_id_list = exclude_tasks.task_id_list
            probset.del_items(exclude_task_id_list, del_by_list=True)
        elif type(cfg_probset.exclude_json) == list:
            for exclude_json in cfg_probset.exclude_json:
                exclude_tasks = HDLBitsProbset()
                exclude_tasks.data = ls.load_json_dict(exclude_json)
                exclude_task_id_list = exclude_tasks.task_id_list
                probset.del_items(exclude_task_id_list, del_by_list=True)
    run_info_path = ls.save_path_setting(config, "dir") + "Chatbench_RunInfo.json"
    run_info = [] 
    for idx, probdata_single in enumerate(probset.data):
        task_id = probdata_single["task_id"]
        print_and_save("\n#################### task %d/%d [%s] ####################" % (idx+1, probset.num, task_id), config)
        run_info_single = pipeline_one_prob(probdata_single, TBgen_prompt_script, config)
        # run_info_single = pipeline_one_prob(probdata_single, stage_template_data, config, "%s/"%(task_id))
        run_info.append(run_info_single)
        # save run info: (write to file every iteration and will overwrite the previous one)
        save_dict_json_form(run_info, run_info_path)
    if config.autoline.onlyrun is None:
        analyzer = al.Analyzer(run_info, config.gpt.model)
        analyzer.run()
        print_and_save(analyzer.messages, config)

def pipeline_one_prob(prob_data:dict, TBgen_prompt_script, config):
    """
    #### output:
    - dict
        - task_id : str (the name of the problem)
        - task_number : int (the number of the problem)
        - sim_pass : bool (whether the simulation is successful. This is only the necessary condition of the correctness of the testbench)
        - TC_pass : bool (whether all test cases passed)
        - debug_iter : int (the number of debug iterations)
        - time : float (the total time of the pipeline)
        - prompt_tokens : int (the number of tokens used in prompt)
        - completion_tokens : int (the number of tokens used in completion)
        - ERROR(incomplete) : bool (whether the pipeline is incomplete)
    """
    task_id = prob_data["task_id"]
    task_NO = prob_data["task_number"]
    header = prob_data["header"]
    DUT_golden = prob_data['module_code']
    TB_golden = prob_data.get("testbench", None)
    mutant_list = prob_data.get("mutants", None)
    gptgen_list = prob_data.get('gptgen_RTL', None)
    full_pass = False
    task_dir = config.save.root + task_id + "/"
    os.makedirs(task_dir, exist_ok=True)
    # pipeline_TBgen/sim:
    with Timer(print_en=False) as TBgen_and_sim_and_eval:
        if config.autoline.onlyrun == "TBgen":
            # TBgen = TaskTBgen(prob_data, TBgen_prompt_script, task_dir, config)
            # TBgen.run(save_code=True)
            TBgen_manager = TaskTBgen_new(prob_data, TBgen_prompt_script, task_dir, config)
            TBgen = TBgen_manager.workflow
            TBgen()
            incomplete_running = True
        elif config.autoline.onlyrun == "TBgensim":
            TBgen_manager = TaskTBgen_new(prob_data, TBgen_prompt_script, task_dir, config)
            TBgen = TBgen_manager.workflow
            TBgen()
            incomplete_running = True
            TBsim = TaskTBsimNew(TBgen, TBgen.TB_code, header, task_dir, task_id, config)
            TBsim.run()
        else:
            # TBgen = TaskTBgen(prob_data, TBgen_prompt_script, task_dir, config)
            # TBgen.run()
            if config.autoline.error_interruption: # for debug
                TBgen_manager = TaskTBgen_new(prob_data, TBgen_prompt_script, task_dir, config)
                TBgen = TBgen_manager.workflow
                TBgen()
                TBsim = TaskTBsimNew(TBgen, TBgen.TB_code, header, task_dir, task_id, config)
                TBsim.run()
                # TB_code = TBgen.TB_code if TBsim.debug_iter_now == 0 else TBsim.TB_code_now
                TBeval = TaskTBeval(task_id, task_dir, TB_gen=TBsim.TB_code_now, TB_golden=TB_golden, DUT_golden=DUT_golden, DUT_mutant_list=mutant_list, DUT_gptgen_list=gptgen_list, pychecker_en=TBsim.pychecker_en, pychecker_code=TBsim.PY_code_now, config=config)
                TBeval.run()
                incomplete_running = False
            else: # normal running
                try:
                    TBgen_manager = TaskTBgen_new(prob_data, TBgen_prompt_script, task_dir, config)
                    TBgen = TBgen_manager.workflow
                    TBgen()
                    TBsim = TaskTBsimNew(TBgen, TBgen.TB_code, header, task_dir, task_id, config)
                    TBsim.run()
                    # TB_code = TBgen.TB_code if TBsim.debug_iter_now == 0 else TBsim.TB_code_now
                    TBeval = TaskTBeval(task_id, task_dir, TB_gen=TBsim.TB_code_now, TB_golden=TB_golden, DUT_golden=DUT_golden, DUT_mutant_list=mutant_list, DUT_gptgen_list=gptgen_list, pychecker_en=TBsim.pychecker_en, pychecker_code=TBsim.PY_code_now, config=config)
                    TBeval.run()
                except Exception as e:
                    incomplete_running = True
                    print_and_save("{{ERROR}} [%s] %s"%(task_id, str(e)), config)            
                else:
                    incomplete_running = False
    TBgen_exist = "TBgen" in locals()
    TBsim_exist = "TBsim" in locals()
    TBeval_exist = "TBeval" in locals()
    info_out = {
        "task_id": task_id,
        "task_number": task_NO,
        "time": round(TBgen_and_sim_and_eval.interval, 2),
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "ERROR(incomplete)": incomplete_running
    }
    if TBgen_exist:
        info_out["prompt_tokens"] += TBgen.tokens["prompt"]
        info_out["completion_tokens"] += TBgen.tokens["completion"]
        if hasattr(TBgen, "circuit_type"):
            info_out["circuit_type"] = TBgen.circuit_type
        if hasattr(TBgen, "checklist_worked"):
            info_out["checklist_worked"] = TBgen.checklist_worked
    if TBsim_exist:
        info_out["prompt_tokens"] += TBsim.tokens["prompt"]
        info_out["completion_tokens"] += TBsim.tokens["completion"]
        info_out.update({
            "Eval0_pass": TBsim.Eval0_pass,
            "Eval0_iv_pass": TBsim.sim_pass,
            "debug_iter_iv": TBsim.debug_iter_iv_now,
            "iv_runing_time": TBsim.iv_runing_time
        })
        if TBsim.pychecker_en:
            info_out.update({
                "Eval0_py_pass": TBsim.py_pass,
                "debug_iter_py": TBsim.debug_iter_py_now,
                "py_runing_time": TBsim.py_runing_time
            })
        
    if TBeval_exist:
        if TBeval.Eval1_exist:
            info_out.update({"Eval1_pass": TBeval.Eval1_pass})
        if TBeval.Eval2_exist:
            info_out.update({
                "Eval2_pass": TBeval.Eval2_pass,
                "Eval2_ratio": "%d/%d"%(len(TBeval.Eval2_passed_mutant_idx), len(prob_data['mutants'])),
                "Eval2_failed_mutant_idxes": TBeval.Eval2_failed_mutant_idx
            })
        if TBeval.Eval2b_exist:
            info_out.update({
                "Eval2b_pass": TBeval.Eval2b_pass,
                "Eval2b_ratio": "%d/%d"%(len(TBeval.Eval2b_passed_mutant_idx), len(prob_data['gptgen_RTL'])),
                "Eval2b_failed_mutant_idxes": TBeval.Eval2b_failed_mutant_idx
            })
    if not incomplete_running:
        full_pass = TBsim.sim_pass and TBeval.Eval1_pass and TBeval.Eval2_pass
        info_out.update({
            "full_pass": full_pass
        })
    # save the info into a json file in problem dir
    save_dict_json_form(info_out, task_dir + "run_info.json")
    return info_out

class TaskTBgen_new():
    # TODO: in the future use pythonized prompt scripts and this class to replace the old TaskTBgen
    """TBgen, in this class we generate tb by calling different python script according to stage_template"""
    def __init__(self, prob_data: dict, TBgen_prompt_script: str, task_dir: str, config):
        self.prob_data = prob_data
        self.prompt_script_name = TBgen_prompt_script
        self.task_dir = task_dir
        self.config = config
        WorkFlowClass = get_script(TBgen_prompt_script)
        self.workflow = WorkFlowClass(
            prob_data = prob_data,
            task_dir = task_dir,
            config = config
        )

    def run(self):
        self.workflow()


class TaskTBsimNew():
    """
    #### input:
    - ivcode_path:
        - the path of iverilog dir (xxx/TB_gen/), will contain all verilog files. generated .vvp will also be saved here
    #### output:
        - dict of the simulation result
            - "sim_pass" : bool (whether the simulation is successful. This is only the necessary condition of the correctness of the testbench)
            - "debug_iter" : int (the number of debug iterations)
            - "sim_out" : str (the output of the simulation)
            - "sim_err" : str (the error of the simulation)
            - "TB_gen_debugged" : str or None (the testbench code after debug)
    #### iverilog_path:
        - the path of iverilog dir, will contain all verilog files. generated .vvp will also be saved here
    #### task_id:
        - the name of the problem, will be used as the name of generated files
    file structure:
    - original
        - task_id.v
        - task_id_tb.v
        - task_id_vlist.txt
        - task_id.vvp
    - debug_1
        - task_id.v
        - task_id_tb.v
        - task_id_vlist.txt
        - task_id.vvp
    - debug_2
        - ...
    """
    def __init__(self, TBgen: BaseScript, TB_code: str, module_header: str, task_dir: str, task_id: str, config):
        self.TBgen = TBgen
        self.TB_code_now = TB_code
        self.module_header = module_header
        self.task_dir = task_dir if task_dir.endswith("/") else task_dir + "/" # for the compatibility with the old version
        self.task_id = task_id
        self.config = config
        self.working_dir = TBgen.TB_code_dir if TBgen.TB_code_dir.endswith("/") else TBgen.TB_code_dir + "/" # will change during the debug process
        self.DUT_code = module_header + "\n\nendmodule\n"
        self.debug_iter_max = config.autoline.debug.max
        self.debug_iter_to_reboot = config.autoline.debug.reboot
        self.proc_timeout = config.autoline.timeout
        # self.debug_iter_now = 0 # this is a counter for both iverilog and python so it is possible to be larger than debug_iter_max
        self.debug_iter_iv_now = 0 
        self.debug_iter_after_reboot_iv = 0 
        self.debug_iter_py_now = 0 
        self.debug_iter_after_reboot_py = 0 
        self.reboot_both = False
        # self.debug_iter_after_reboot = 0
        # pychecker related
        self.pychecker_en = self.TBgen.Pychecker_en
        self.PY_code_now = ""
        if self.pychecker_en:
            self.TBout_content = "" # will get after the last iverilog run
            self.PY_code_now = self.TBgen.Pychecker_code
            self.py_fail_reboot_both_iter = config.autoline.debug.py_rollback # will reboot both iv and py if python simulation failed xxx times
            self.py_debug_focus = self.TBgen.py_debug_focus 
        # infos
        self.sim_pass = False # this should be com_pass, but it is too late to change it now
        self.py_pass = False
        self.Eval0_pass = False
        self.iverilog_info = None
        self.reboot_both_times = 0
        self.iv_runing_time = 0.0 # the time of running the last iverilog
        self.py_runing_time = 0.0 # the time of running the last python
        self.tokens = {"prompt": 0, "completion": 0}

    # def run(self):
    #     self.run_iverilog()
    #     if self.pychecker_en:
    #         if self.sim_pass:
    #             self.run_python()
    #         else:
    #             raise ValueError("TBsim: iverilog failed, python simulation is not allowed.")
            
    def run(self):
        if not self.pychecker_en:
            self.run_iverilog()
            self.Eval0_pass = self.sim_pass
        else:
            exit_en = False
            while (not exit_en):
                self.run_iverilog()
                if self.sim_pass:
                    self.run_python()
                    # if (self.sim_pass and self.py_pass) or self.exceed_max_debug:
                    if not self.reboot_both:
                        exit_en = True
                else:
                    exit_en = True
                    self.Eval0_pass = False
                    raise ValueError("TBsim: iverilog failed, python simulation is not allowed.")
            self.Eval0_pass = self.sim_pass and self.py_pass
        self._print_and_save("[%s] TBsim finished : %s! (%s)"%(self.task_id, self.Eval0_pass, get_time()))

    def run_iverilog(self):
        """
        - the main function of TBsim
        """
        if not self.reboot_both:
            # this will only be called at the first time of runing run_iverilog
            self._save_code_run_iverilog()
            self.sim_pass = self.iverilog_info[0]
        while (self.debug_iter_iv_now < self.debug_iter_max) and (not self.sim_pass):
            self.debug_iter_iv_now += 1
            if self.debug_iter_after_reboot_iv < self.debug_iter_to_reboot:
                self.debug_iter_after_reboot_iv += 1
                self._debug_iv()
            else:
                self._reboot_iv()
            self.sim_pass = self.iverilog_info[0]
            self.reboot_both = False
        if self.reboot_both:
            # this means didn't enter the while, because debug_iter_max is already reached
            self._print_and_save("[%s] iverilog compilation (reboot from python) : failed! iverilog exceeded max debug iteration (%s) (%s)"%(self.task_id, self.debug_iter_max, get_time()))
        if self.sim_pass:
            self._print_and_save("[%s] iverilog compilation : passed! (%s)"%(self.task_id, get_time()))
        else:
            self._print_and_save("[%s] iverilog compilation : failed! exceeded max debug iteration (%s) (%s)"%(self.task_id, self.debug_iter_max, get_time()))
        # self.sim_out = self.iverilog_info[4]["out"] if self.iverilog_info[4] is not None else ""
        # self.sim_err = self.iverilog_info[-1]
        # clean .vcd wave files
        self.clean_vcd()
    
    def run_python(self):
        # read the TBout.txt into TBout_content in working_dir
        with open(self.TBout_path, "r") as f:
            self.TBout_content = f.read()
        self.debug_iter_after_reboot_py = 0
        py_rollback = 0 # local variable
        self._save_code_run_python()
        # self.debug_iter_py_now
        while (self.debug_iter_py_now < self.debug_iter_max) and (not self.python_info[0]):
            if (not self.python_info[0]) and (py_rollback >= self.py_fail_reboot_both_iter):
                # +1: debug py fail + [generated py fail]
                self.reboot_both = True
                break
            py_rollback += 1
            self.debug_iter_py_now += 1
            if self.debug_iter_after_reboot_py < self.debug_iter_to_reboot:
                self.debug_iter_after_reboot_py += 1
                self._debug_py()
            else:
                self._reboot_py()
            # self._reboot_py() # only reboot, no debugging because python debugging is much harder than verilog
            # currently debug_py doesn't support reboot
        if self.reboot_both:
            self.py_pass = False
            self.sim_pass = False
            self.debug_iter_after_reboot_iv = self.debug_iter_to_reboot
            self._print_and_save("[%s] python simulation : failed! will reboot both iverilog and python (%s)"%(self.task_id, get_time()))
        elif self.python_info[0]:
            self.py_pass = True
            self._print_and_save("[%s] python simulation : passed! (%s)"%(self.task_id, get_time()))
        else:
            self.py_pass = False
            self._print_and_save("[%s] python simulation : failed! exceeded max debug iteration (%s) (%s)"%(self.task_id, self.debug_iter_max, get_time()))
        self.py_out = self.python_info[1]["out"] if self.python_info[1] is not None else ""
        self.py_err = self.python_info[-1]

    def _debug_iv(self):
        with Timer(print_en=False) as debug_time:
            self._print_and_save("\n[%s] iverilog simulation failed! Debuging... (debug_iter = %s, time: %s)"%(self.task_id, self.debug_iter_iv_now, get_time()))
            self.working_dir = self.task_dir + "debug_%s/" % (self.total_debug_iter_now)
            os.makedirs(self.working_dir, exist_ok=True)
            debug_prompt = self._debug_prompt_gen_iv()
            debug_message = [{"role": "user", "content": debug_prompt}]
            gpt_response, info = gpt.llm_call(debug_message, self.config.gpt.model, self.config.gpt.key_path)
            debug_message = info["messages"]
            self.TB_code_now = gpt.extract_code(gpt_response, "verilog")[-1]
            self.TB_code_now = self.del_linemark(self.TB_code_now)
            self._save_code_run_iverilog()
        self._print_and_save("[%s] %s: verilog DEBUG finished (%ss used, time: %s)" % (self.task_id, self.debug_iter_info("iv"), round(debug_time.interval, 2), get_time()))
        self.tokens["prompt"] += info["usage"]["prompt_tokens"]
        self.tokens["completion"] += info["usage"]["completion_tokens"]
        ls.save_messages_to_txt(debug_message, self.working_dir+"debug_messages.txt")

    def _reboot_iv(self):
        # change TBgen's code dir
        with Timer (print_en=False) as reboot_time:
            self._print_and_save("\n[%s] iverilog simulation failed! Rebooting... (debug_iter = %s, time: %s)"%(self.task_id, self.debug_iter_iv_now, get_time()))
            self.working_dir = self.task_dir + "debug_%s_reboot/" % (self.total_debug_iter_now)
            os.makedirs(self.working_dir, exist_ok=True)
            self.TBgen.run_reboot(self.working_dir, reboot_mode="TB")
            self.TB_code_now = self.TBgen.TB_code
            self._save_code_run_iverilog()
        self._print_and_save("[%s] %s: verilog REBOOT finished (%ss used, time: %s)" % (self.task_id, self.debug_iter_info("iv"), round(reboot_time.interval, 2), get_time()))
        # the tookens will be added into TBgen's tokens count, we don't count it again here.
        # reset reboot counter
        self.debug_iter_after_reboot_iv = 0

    def _debug_py(self):
        with Timer(print_en=False) as debug_time:
            self._print_and_save("\n[%s] python compilation failed! Debuging python... (debug_iter = %s, time: %s)"%(self.task_id, self.debug_iter_py_now, get_time()))
            self.working_dir = self.task_dir + "debug_%s/" % (self.total_debug_iter_now)
            os.makedirs(self.working_dir, exist_ok=True)
            # run gpt
            debug_prompt = self._debug_prompt_gen_py()
            debug_message = [{"role": "user", "content": debug_prompt}]
            gpt_response, info = gpt.llm_call(debug_message, self.config.gpt.model, self.config.gpt.key_path)
            debug_message = info["messages"]
            self.PY_code_now = gpt.extract_code(gpt_response, "python")[-1]
            self.PY_code_now = self.del_linemark(self.PY_code_now)
            if self.py_debug_focus: # currently only support pychecker SEQ mode
                self.PY_code_now = self._py_focus(self.PY_code_now, before=False)
            self._save_code_run_python()
        self._print_and_save("[%s] %s: python DEBUG finished (%ss used, time: %s)" % (self.task_id, self.debug_iter_info("py"), round(debug_time.interval, 2), get_time()))
        self.tokens["prompt"] += info["usage"]["prompt_tokens"]
        self.tokens["completion"] += info["usage"]["completion_tokens"]
        ls.save_messages_to_txt(debug_message, self.working_dir+"debug_messages.txt")

    def _reboot_py(self):
        # change TBgen's code dir
        with Timer (print_en=False) as reboot_time:
            self._print_and_save("\n[%s] python compilation failed! Rebooting... (debug_iter = %s, time: %s)"%(self.task_id, self.debug_iter_py_now, get_time()))
            self.working_dir = self.task_dir + "debug_%s_reboot/" % (self.total_debug_iter_now)
            os.makedirs(self.working_dir, exist_ok=True)
            self.TBgen.run_reboot(self.working_dir, reboot_mode="PY")
            self.PY_code_now = self.TBgen.Pychecker_code
            self._save_code_run_python()
        self._print_and_save("[%s] %s: python REBOOT finished (%ss used, time: %s)" % (self.task_id, self.debug_iter_info("py"), round(reboot_time.interval, 2), get_time()))
        # the tookens will be added into TBgen's tokens count, we don't count it again here.
        # reset reboot counter
        self.debug_iter_after_reboot_py = 0 

    def _save_code_run_iverilog(self):
        with open(self.TB_path, "w") as f:
            f.write(self.TB_code_now)
        with open(self.DUT_path, "w") as f:
            f.write(self.DUT_code)
        with Timer(print_en=False) as iverilog_time:
            self.iverilog_info = iv.iverilog_call_and_save(self.working_dir, silent=True, timeout=self.proc_timeout)
        self.iv_runing_time = round(iverilog_time.interval, 2)
        self.error_message_now = self.iverilog_info[-1]
        if "program is timeout" in self.error_message_now:
            # if the error message is timeout, we will delete the TBout.txt
            # this is to avoid the situation that infinite loop produces a large TBout.txt
            if os.path.exists(self.TBout_path):
                os.remove(self.TBout_path)
            self.clean_vvp()
    
    def _save_code_run_python(self):
        with open(self.PY_path, "w") as f:
            f.write(self.PY_code_now)
        with open(self.TBout_path, "w") as f:
            f.write(self.TBout_content)
        with Timer(print_en=False) as python_time:
            self.python_info = py.python_call_and_save(pypath=self.PY_path, silent=True, timeout=self.proc_timeout)
        self.py_runing_time = round(python_time.interval, 2)
        self.error_message_now = self.python_info[-1]

    def _debug_prompt_gen_iv(self):
        debug_prompt = DEBUG_TEMPLATE + "\n previous testbench with error:\n" + self.add_linemark(self.TB_code_now) + "\n compiling error message:\n" + self.error_message_now
        return debug_prompt
    
    def _debug_prompt_gen_py(self):
        if self.py_debug_focus:
            py_code = self._py_focus(self.PY_code_now, before=True)
        else:
            py_code = self.PY_code_now
        if not ("program is timeout" in self.error_message_now):
            self.error_message_now = self._py_error_message_simplify(self.error_message_now)
        debug_prompt = DEBUG_TEMPLATE_PY + "\n previous python code with error:\n" + self.add_linemark(py_code) + "\n compiling error message:\n" + self.error_message_now
        return debug_prompt
    
    def _py_focus(self, code:str, before:bool):
        """
        - code: the code under debug / after debug
        - before: True, if before debug, will split the code; False, if after debug, will restore the code
        """
        KEY_WORD = "\ndef check_dut"
        if before:
            if KEY_WORD not in code:
                py_code_focus = code
                self.py_code_nofocus = ""
            else:
                py_code_focus = code.split(KEY_WORD)[0]
                self.py_code_nofocus = KEY_WORD + code.split(KEY_WORD)[1]
            return py_code_focus
        else:
            return code + self.py_code_nofocus

    @staticmethod
    def _py_error_message_simplify(error_message:str, error_depth:int=1):
        """
        - extract the key point of python error message
        - error_depth: how many (how deep, from bottom to top) error messages to extract
        """
        msg_lines = error_message.split("\n")
        msg_out = ""
        for line in reversed(msg_lines):
            msg_out = line + "\n" + msg_out
            if "File" in line:
                error_depth -= 1
                if error_depth == 0:
                    break
        return msg_out

    @property
    def exceed_max_debug(self):
        return (self.debug_iter_iv_now >= self.debug_iter_max) or (self.debug_iter_py_now >= self.debug_iter_max)

    @property
    def total_debug_iter_now(self):
        return self.debug_iter_iv_now + self.debug_iter_py_now

    @property
    def TB_path(self):
        return self.working_dir + self.task_id + "_tb.v"
    
    @property
    def DUT_path(self):
        return self.working_dir + self.task_id + ".v"
    
    @property
    def PY_path(self):
        return self.working_dir + self.task_id + "_tb.py"
    
    @property
    def TBout_path(self):
        return self.working_dir + "TBout.txt"
    
    def debug_iter_info(self, type):
        """return debug iter info string. Type: "iv" or "py" """
        if self.pychecker_en:
            if type == "iv":
                return "verilog iter - %d/%d, total - %d/%d"%(self.debug_iter_iv_now, self.debug_iter_max, self.total_debug_iter_now, self.debug_iter_max*2)
            elif type == "py":
                return "python tier - %d/%d, total - %d/%d"%(self.debug_iter_py_now, self.debug_iter_max, self.total_debug_iter_now, self.debug_iter_max*2)
            else:
                raise ValueError("TaskTBsim.debug_iter_info(type): type should be 'iv' or 'py'")
        else:
            # only iverilog
            return "debug iter %d/%d"%(self.debug_iter_iv_now, self.debug_iter_max)

    @staticmethod
    def add_linemark(code: str):
        """add the line mark (1., 2., ...) to the code at the beginning of each line"""
        code = code.split("\n")
        code = [str(i+1) + ". " + line for i, line in enumerate(code)]
        return "\n".join(code)
    
    @staticmethod
    def del_linemark(code: str):
        """delete the line mark at the begening of each line if line mark exists"""
        code = code.split("\n")
        if code[1].split(".")[0].isdigit(): # use code[1] in case the first line is empty
            code = [line.split(". ")[1:] for line in code]
            for i, line in enumerate(code):
                code[i] = ". ".join(line)
        return "\n".join(code)
    
    def clean_vcd(self):
        """clean the .vcd files in the task_dir"""
        clean_dir = self.task_dir[:-1] if self.task_dir.endswith("/") else self.task_dir
        for root, dirs, files in os.walk(clean_dir):
            for file in files:
                if file.endswith(".vcd"):
                    os.remove(os.path.join(root, file))
    
    def clean_vvp(self):
        """clean the .vvp files in the task_dir"""
        clean_dir = self.task_dir[:-1] if self.task_dir.endswith("/") else self.task_dir
        for root, dirs, files in os.walk(clean_dir):
            for file in files:
                if file.endswith(".vvp"):
                    os.remove(os.path.join(root, file))

    def _print_and_save(self, message):
        ls.print_and_save(message, self.config)

class TaskTBeval():
    """
    ### description
    - this is the evaluation stage of our pipeline; the priority of this stage is that TB is generated and the empty DUT compilation is passed;
    - please use `try` to catch the exception of this function
    #### input
    - task_id: the name of the problem
    - root_dir: the dir of one problem
    - TB_gen: the testbench under evaluation (str)
    - TB_golden: the golden testbench (str)
    - DUT_golden: the golden RTL DUT (str)
    - DUT_mutant_list: the list of RTL DUT mutants modified from DUT_golden;[str]        
    #### output
    - dict
        - "Eval1_pass" : bool (whether the golden RTL checking passed)
        - "Eval2_pass" : bool (whether the golden TB comparison on RTL mutants passed)
        - "Eval2_failed_mutant_idxes" : list of int (the index of the failed mutants)
    """
    """main structure: run(), run_Eval1(), run_Eval2()"""
    def __init__(self, task_id: str, task_dir: str, TB_gen: str, config:object, TB_golden:str=None, DUT_golden:str=None, DUT_mutant_list:list=None, DUT_gptgen_list:list = None, pychecker_en:bool = False, pychecker_code:str = ""):
        self.task_id = task_id
        self.task_dir = task_dir
        self.TB_gen = TB_gen
        self.TB_golden = TB_golden
        self.DUT_golden = DUT_golden
        self.DUT_mutant_list = DUT_mutant_list
        self.DUT_gptgen_list = DUT_gptgen_list
        self.config = config
        self.pychecker_en = pychecker_en
        self.TB_gen_mode = "TB_gen" if not self.pychecker_en else "Pychecker"
        self.pychecker_code = pychecker_code
        self.working_dir = ""
        # Eval1 related
        self.Eval1_exist = False
        self.Eval1_dir = task_dir + "eval1_GoldenRTL/"
        self.Eval1_results = None
        self.Eval1_pass = None
        # Eval2 related
        self.Eval2_exist = False
        self.Eval2_dir = task_dir + "eval2_GoldenTB_and_mutants/"
        self.Eval2_pass = None
        self.Eval2_failed_mutant_idx = None
        self.Eval2_passed_mutant_idx = None
        # Eval2b related
        self.Eval2b_exist = False
        self.Eval2b_dir = task_dir + "eval2b_GPTgenTB/"
        self.Eval2b_pass = None
        self.Eval2b_failed_mutant_idx = None
        self.Eval2b_passed_mutant_idx = None

    def run(self):
        # Eval 1
        if self.DUT_golden is not None:
            self.run_Eval1()
        if self.Eval1_pass:
            # Eval 2
            if self.TB_golden is not None and self.DUT_mutant_list is not None:
                self.run_Eval2(mode="mutant")
            # Eval 2b
            if self.TB_golden is not None and self.DUT_gptgen_list is not None:
                self.run_Eval2(mode="gptgen")
        else:
            print_and_save("[%s] Eval 2/2b is skipped because Eval 1 failed" % (self.task_id), self.config) 
        self.clean_wave_vcd() # some golden TBs may generate wave.vcd files
    
    def run_Eval1(self):
        silent = True
        ### Eval 1: Golden RTL checking
        print_and_save("\n[%s] Eval 1: Golden RTL checking begins" % (self.task_id), self.config)
        self.Eval1_pass = self.run_testbench(self.Eval1_dir, self.TB_gen, self.DUT_golden, self.TB_gen_mode, self.pychecker_code, raise_when_fail=True)
        print_and_save("[%s] Eval 1: Golden RTL checking %s! (%s)" % (self.task_id, "passed" if self.Eval1_pass else "failed", get_time()), self.config)
        self.Eval1_exist = True

    def run_Eval2(self, mode:str="mutant"):
        """ mode: "mutant" or "gptgen" """
        silent = True
        assert mode in ["mutant", "gptgen"], "Invalid mode in run_Eval2: " + mode
        if mode == "mutant": # Eval2
            print_str = "Eval 2: Golden TB checking on RTL mutants"
            mutant_subdir_name = "mutatnt"
            DUT_list = self.DUT_mutant_list
            eval_dir = self.Eval2_dir
        elif mode == "gptgen": # Eval2b
            print_str = "Eval 2b: Golden TB checking on GPT generated RTL codes"
            mutant_subdir_name = "gptgen_DUT"
            DUT_list = self.DUT_gptgen_list
            eval_dir = self.Eval2b_dir
        ### Eval 2: Golden TB comparison on RTL mutants
        print_and_save("[%s] %s" % (self.task_id, print_str), self.config)
        mutant_results = []
        for idx, DUT_mutant in enumerate(DUT_list):
            mutant_subdir = eval_dir + "%s_%d/"%(mutant_subdir_name, idx+1)
            GoldenTB_subsubdir = mutant_subdir + "GoldenTB/"
            GenedTB_subsubdir = mutant_subdir + "GeneratedTB/"
            try: #in case the mutant has syntax error
                TBgolden_pass = self.run_testbench(GoldenTB_subsubdir, self.TB_golden, DUT_mutant, "TB_golden")
            except:
                TBgolden_pass = False
            try:
                TBgen_pass = self.run_testbench(GenedTB_subsubdir, self.TB_gen, DUT_mutant, self.TB_gen_mode, self.pychecker_code)
            except:
                TBgen_pass = False
            if not TBgolden_pass and not TBgen_pass:
                mutant_pass = True
            elif TBgolden_pass and TBgen_pass:
                mutant_pass = True
            else:
                mutant_pass = False
            mutant_results.append(mutant_pass)
        eval_pass = all(mutant_results)
        failed_mutant_idx = [idx + 1 for idx, result in enumerate(mutant_results) if not result]
        passed_mutant_idx = [idx + 1 for idx, result in enumerate(mutant_results) if result]
        if mode == "mutant":
            self.Eval2_pass, self.Eval2_failed_mutant_idx, self.Eval2_passed_mutant_idx, self.Eval2_exist = eval_pass, failed_mutant_idx, passed_mutant_idx, True
        elif mode == "gptgen":
            self.Eval2b_pass, self.Eval2b_failed_mutant_idx, self.Eval2b_passed_mutant_idx, self.Eval2b_exist = eval_pass, failed_mutant_idx, passed_mutant_idx, True
        result = "perfectly passed" if eval_pass else ("finished (%d/%d)" % (len(passed_mutant_idx), len(mutant_results)))
        print_and_save("[%s] %s %s! (%s)" % (self.task_id, print_str, result, get_time()), self.config)

    def run_testbench(self, dir, TB_code, DUT_code, TB_type, pychecker_code = "", raise_when_fail = False):
        """
        it has two mode: pychecker mode or verilog testbench mode
        -input:
            - dir: the dir to save the TB, DUT and pychecker code
            - TB_code: str; the testbench code
            - DUT_code: str; the DUT code
            - TB_type: str: TB_gen, TB_golden, Pychecker
            - pychecker_code: str; the pychecker code
        - output:
            - pass: bool; if the DUT passed the testbench
        """
        # iverilog part
        # save the TB and DUT
        assert TB_type in ["TB_gen", "TB_golden", "Pychecker"], "Invalid TB_type in run_testbench: " + TB_type
        os.makedirs(dir, exist_ok=True)
        self.working_dir = dir
        with open(self.TB_path, "w") as f:
            f.write(TB_code)
        with open(self.DUT_path, "w") as f:
            f.write(DUT_code)
        iv_run_info = iv.iverilog_call_and_save(dir, silent=True)
        if raise_when_fail:
            assert iv_run_info[0], "%s Iverilog Compilation Failed: the PREREQUISITE of 'Evaluation' is no syntactic error from Testbench!!!"%(TB_type)
        # pychecker part (if enabled)
        if TB_type == "Pychecker":
            with open(self.PY_path, "w") as f:
                f.write(pychecker_code)
            py_run_info = py.python_call_and_save(pypath=self.PY_path, silent=True)
            if raise_when_fail:
                assert py_run_info[0], "%s Python Compilation Failed: the PREREQUISITE of 'Evaluation' is no syntactic error from Python code!!!"%(TB_type)
            # check if the DUT passed the testbench
            TC_pass = self.TC_pass_from_TC_out(sim_pass=True, sim_out=py_run_info[1]["out"], TB_type="Pychecker") & iv_run_info[0] & py_run_info[0]
        else:
            TC_pass = self.TC_pass_from_TC_out(sim_pass=True, sim_out=iv_run_info[4]["out"], TB_type=TB_type) & iv_run_info[0]
        return TC_pass

    def clean_wave_vcd(self):
        """clean the .vcd files in the task_dir"""
        clean_dir = self.task_dir[:-1] if self.task_dir.endswith("/") else self.task_dir
        for root, dirs, files in os.walk(clean_dir):
            for file in files:
                # clean wave.vcd
                if file.endswith(".vcd"):
                    os.remove(os.path.join(root, file))

    @property
    def TB_path(self):
        return self.working_dir + self.task_id + "_tb.v"
    
    @property
    def DUT_path(self):
        return self.working_dir + self.task_id + ".v"
    
    @property
    def PY_path(self):
        return self.working_dir + self.task_id + "_tb.py"

    @staticmethod
    def TC_pass_from_TC_out(sim_pass: bool, sim_out: str, TB_type="TB_gen"):
        """
        get the information if DUT passed all the test cases from the testbench
        #### input
        - sim_pass: bool; if TB passed the compilation. if not, will return False without check
        - sim_out: the simulation output message;
        - TB_ty: "TB_gen" or "TB_golden" or "Pychecker"; the type of the testbench
        """
        if not sim_pass:
            return False
        assert TB_type in ["TB_gen", "TB_golden", "Pychecker"], "Invalid TB_type during 'TC_pass_from_TC_out': " + TB_type
        tc_pass_check_list_dict = {"TB_gen": TC_PASS_CHECK_LIST_TB_GEN, "TB_golden": TC_PASS_CHECK_LIST_TB_GOLDEN, "Pychecker": TC_PASS_CHECK_LIST_PYCHECKER}
        tc_pass_check_list = tc_pass_check_list_dict[TB_type]
        for check_str in tc_pass_check_list:
            if check_str in sim_out:
                return True
        return False


if __name__ == "__main__":
    raise RuntimeError("you cannot run autoline.py directly!")
