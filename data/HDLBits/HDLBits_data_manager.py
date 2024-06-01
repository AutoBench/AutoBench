"""
Description :   This script is used to merge the data from VerilogEval (originally from HDLBits). Run this script in the root directory of the project.
Author      :   AutoBench's Author (Anonymous Email)
Time        :   2023/12/06 15:50:33
LastEdited  :   2024/5/21 23:00:10
"""

import sys
if __name__ == "__main__":
    sys.path.append(".")
import random
import LLM_call as gpt
import loader_saver as ls
from data.probset import HDLBitsProbset
from copy import deepcopy
from loader_saver import load_json_lines, save_json_lines, find_line_jsonl


VerilogDescription_Human_path = "data/HDLBits/original_data_human/VerilogDescription_Human.jsonl"
VerilogEval_Human = "data/HDLBits/original_data_human/VerilogEval_Human.jsonl"
FATHER_DATA_PATH = "data/HDLBits/HDLBits_data.jsonl"
MERGED_DATA_PATH = "data/HDLBits/HDLBits_data.jsonl"
CIRCUIT_TYPE_PATH = "data/HDLBits/HDLBits_circuit_type.jsonl"
REPORT_PATH = "data/HDLBits/HDLBits_data_report.txt"
MUTANT_TEMPLATE_PATH = "config/templates/script_template/mutant_template.txt"
LLM_MODEL = "gpt-4-turbo-2024-04-09"

def main():
    pass
    
## analyze the HDLBits json data
class HDLBitsManager(HDLBitsProbset):
    def __init__(self, jsonl_path:str, report_path=None, more_info_paths:list=[], only_tasks=None, exclude_tasks=[], filter_content={}):
        super().__init__(jsonl_path, more_info_paths=more_info_paths, only_tasks=only_tasks, exclude_tasks=exclude_tasks, filter_content=filter_content)
        self.jsonl_path = jsonl_path
        if report_path is None:
            # save in the same directory as the jsonl file
            report_path = self.jsonl_path[:self.jsonl_path.rfind(".")] + "_report.txt"
        self.report_path = report_path
        self.report_txt = ""
        pass

    @property
    def additional_data(self):
        if not hasattr(self, "_additional_data"):
            self._additional_data = []
            for data in self.data:
                self._additional_data.append({
                    "task_id": data["task_id"]
                    })
        return self._additional_data
    
    def add_info_additional_data(self, task_id, info_key, info_value):
        self.additional_data
        for data in self._additional_data:
            if data["task_id"] == task_id:
                data[info_key] = info_value
                return
        raise ValueError("task_id %s not found!!!" % (task_id))

    def load_info_additional_data(self, additional_data_path):
        load_additional_data = ls.load_json_lines(additional_data_path)
        for data in load_additional_data:
            try:
                for key, value in data.items():
                    if key != "task_id":
                        self.add_info_additional_data(data["task_id"], key, value)
            except:
                print("error in loading additional data at task_id: %s" % (data["task_id"]))
        print("additional data loaded!")

    # def merge_additional_data(self):
    #     """merge additional data into the original data"""
    #     for data in self.data:
    #         for add_data in self._additional_data:
    #             if data["task_id"] == add_data["task_id"]:
    #                 for key, value in add_data.items():
    #                     if key != "task_id":
    #                         data[key] = value
    #     save_path = self.jsonl_path.replace(".jsonl", "_plus.jsonl")
    #     ls.save_json_lines(self.data, save_path)
    #     print("additional data merged!")

    def save_report(self):
        with open(self.report_path, 'w') as f:
            f.write(self.report_txt)

    def access_data(self, data_name):
        """
        return a dict. dict format: {task_id: data}
        original self.data format: [{"task_id": task_id, "data_1": data_1, "data_2": data_2, ...}, ...]
        """        
        return {i["task_id"]: i[data_name] for i in self.data}
    

    
    def task_RTL_token_num_analysis(self):
        """
        analyze the RTL token number of each task_id and add the result to the data
        """
        for i in self.data:
            i["RTL_token_num"] = gpt.num_tokens_from_string(i["module_code"]) + gpt.num_tokens_from_string(i["header"])
        token_num_data = self.access_data("RTL_token_num")
        ## analyze the token number: min, max, average, and the name of the task_id
        token_num_list = list(token_num_data.values())
        self.report_txt += "////////// token number analysis //////////\n"
        self.report_txt += "total number of tasks: %d\n" % (len(token_num_list))
        self.report_txt += "min token number: %d\n" % (min(token_num_list))
        self.report_txt += "min token task_id: %s\n" % (list(token_num_data.keys())[token_num_list.index(min(token_num_list))])
        self.report_txt += "max token number: %d\n" % (max(token_num_list))
        self.report_txt += "max token task_id: %s\n" % (list(token_num_data.keys())[token_num_list.index(max(token_num_list))])
        self.report_txt += "average token number: %.2f\n" % (sum(token_num_list) / len(token_num_list))
        ## print the distribution of the token number: from 0 to 800, every 50
        token_num_distribution = [0] * 17
        for i in token_num_list:
            token_num_distribution[i//50] += 1
        # print it in a table
        self.report_txt += "token number distribution:\n"
        self.report_txt += "token number\tcount\n"
        for i in range(17):
            self.report_txt += "%d\t\t%d\n" % (i*50, token_num_distribution[i])
        self.report_txt += "\n\n"
        print("RTL token number analysis finished!")

    def task_miniset_gen(self, mini_set_size=20, save_path=None, suffix="miniset"):
        """
        generate a mini set of the data. the mini set size is determined by mini_set_size. data is randomly selected.
        """
        mini_set = random.sample(self.data, mini_set_size)
        if save_path is None:
            # save the mini set in the same directory as the jsonl file.
            save_path = self.jsonl_path[:self.jsonl_path.rfind(".")] + "_%s.jsonl"%(suffix)
        save_json_lines(mini_set, save_path)

    def task_RTL_gen(self, template_path, save_path=None, num_RTL = 10, gpt_model = LLM_MODEL):
        """
        generate RTL code for the tasks in the data.
        """
        if save_path is None:
            # save the mutants in the same directory as the jsonl file.
            save_path = self.jsonl_path[:self.jsonl_path.rfind(".")] + "_RTL.jsonl"
        # load the template (txt)
        with open(template_path, 'r') as f:
            template = f.read()
        # generate the mutants
        new_list = []
        usages = []
        idx = 0
        for data_i in self.data:
            out_dict = {"task_id": data_i["task_id"]}
            prompt_i = template
            prompt_i = prompt_i.replace("{$problem description from HDLBits$}", data_i["description"])
            prompt_i = prompt_i.replace("{$header from HDLBits$}", data_i["header"])
            message_in = [{"role": "user", "content": prompt_i}]
            rtl_list = []
            for i in range(num_RTL):
                response, info = gpt.llm_call(message_in, gpt_model, "config/key_API.json", temperature=0.8)
                rtl_list.append(gpt.extract_code(response, "verilog")[-1])
                usages.append(info["usage"])
            out_dict["RTL_code"] = rtl_list
            new_list.append(out_dict)
            idx += 1
            print("%d task(s) finished!" % (idx))
            save_json_lines(new_list, save_path)
        print("RTL generation finished!")
        cost = gpt.cost_calculator(usages)
        print("total tokens used: $%.4f\n" % (cost))

    def task_mutant_gen(self, template_path, save_path=None, num_mutants=10):
        """
        generate mutants for the tasks in the data.
        """
        from config.config import GPT_MODELS
        if save_path is None:
            # save the mutants in the same directory as the jsonl file.
            save_path = self.jsonl_path[:self.jsonl_path.rfind(".")] + "_mutants.jsonl"
        # load the template (txt)
        with open(template_path, 'r') as f:
            template = f.read()
        # template contains special character {$n$}, replace it with num_mutants (int)
        template = template.replace("{$n$}", str(num_mutants))
        # generate the mutants
        new_list = []
        usages = []
        idx = 0
        for data_i in self.data:
            dict = {"task_id": data_i["task_id"]}
            prompt_i = template
            prompt_i = prompt_i.replace("{$problem description from HDLBits$}", data_i["description"])
            prompt_i = prompt_i.replace("{$RTL code from HDLBits$}", data_i["module_code"])
            message_in = [{"role": "user", "content": prompt_i}]
            response, info = gpt.llm_call(message_in, GPT_MODELS["4"], "config/key_API.json", temperature=0.8)
            mutant_list = gpt.extract_code(response, "verilog")
            dict["mutants"] = mutant_list
            new_list.append(dict)
            idx += 1
            print("%d task(s) finished!" % (idx))
            save_json_lines(new_list, save_path) # save the mutants every time a task is finished
        print("Mutants generation finished!")

    def task_find_xxx_in_xxx(self, keyword, content_name="module_code", show_task_id=False):
        """
        input:
        - keyword: the keyword to be found
        - content_name: the name of the content to be searched. default: "module_code"
        - show_task_id: whether to show the task_id of the task containing the keyword. default: False
        """
        count = 0
        for prob in self.data:
            if keyword in prob.get(content_name, ""):
                if show_task_id:
                    print(prob["task_id"])
                count += 1
        print("%s in %s count: %d" % (keyword, content_name, count))

    def task_circuit_type_gen(self):
        """
        classify the tasks into COM or SEQ according to `module_code`
        """
        def get_CMB_or_SEQ_from_GPT(module_code, description):
            """
            ask GPT to classify the module_code into COM or SEQ
            """
            prompt = "Please classify the following verilog code into combinational circuit or sequential circuit:\n" + module_code + "\nthe circuit description is:\n" + description + "\n IMPORTANT: please only reply one word as the response. If this verilog code is a combinational circuit, please reply 'CMB'. If this verilog code is a sequential circuit, please reply 'SEQ'. \nVERY IMPORTANT: DO NOT reply anything else."
            system_message = "You are a very smart AI, please classify the following verilog code into combinational circuit or sequential circuit. You already have the knowledge to do this."
            message_in = [{"role": "user", "content": prompt}]
            response, info = gpt.llm_call(message_in, GPT_MODEL, "config/key_API.json", temperature=0.5, system_message=system_message)
            return response, info
        # classify the tasks
        ITER_NUM = 2
        GPT_MODEL = "gpt-4-0125-preview"
        SAVE_PATH = self.jsonl_path.replace("data", "circuit_type")
        total_tokens = 0
        total_CMBs = 0
        total_SEQs = 0
        total_unknowns = 0
        unknown_list = []
        for prob in self.data:
            CMB, SEQ = 0, 0
            response_list = []
            for i in range(ITER_NUM):
                response, info = get_CMB_or_SEQ_from_GPT(prob["module_code"], prob["description"])
                response_list.append(response)
                total_tokens += info["usage"]["total_tokens"]
                if "CMB" in response:
                    CMB += 1
                elif "SEQ" in response:
                    SEQ += 1
                if CMB > (ITER_NUM/2.0) or SEQ > (ITER_NUM/2.0):
                    break
            if CMB > SEQ:
                prob["circuit_type"] = "CMB"
                total_CMBs += 1
            elif CMB < SEQ:
                prob["circuit_type"] = "SEQ"
                total_SEQs += 1
            else:
                prob["circuit_type"] = "UNKNOWN"
                total_unknowns += 1
                unknown_list.append(prob["task_id"])
            # save the result into addtional data
            self.add_info_additional_data(prob["task_id"], "circuit_type", prob["circuit_type"])
            ls.save_json_lines(self.additional_data, SAVE_PATH)
            print("%s: %s" % (prob["task_id"], prob["circuit_type"]))
        # save the result into the report
        self.report_txt += "////////// COM or SEQ classification //////////\n"
        self.report_txt += "total tokens used: %d\n" % (total_tokens)
        self.report_txt += "total CMBs: %d\n" % (total_CMBs)
        self.report_txt += "total SEQs: %d\n" % (total_SEQs)
        self.report_txt += "total unknowns: %d\n" % (total_unknowns)
        self.report_txt += "unknown task_id list: %s\n" % (unknown_list)
        self.report_txt += "\n\n"
        self.save_report()
        print("COM or SEQ classification finished!")

    def task_return_task_id_list(self):
        """
        return the list of task_id
        """
        return [i["task_id"] for i in self.data]

    def task_circuit_type_gen_only_description(self, save_path, step2_algorithm=True):
        # we need circuit_type information to check the correctness
        model = "gpt-4-turbo-2024-04-09"
        txt_out = ""
        unmatched = 0
        tokens = 0
        if not ("circuit_type" in self.data[0].keys()):
            raise ValueError("circuit_type information not found!")
        for task in self.data:
            # step 1, generate the RTL code
            prompt = "Please generate the verilog RTL code according to the following description and header information:\nproblem description" + task["description"] + "\nRTL header:\n" + task["header"] + "\n\nplease only reply verilog codes, no other words."
            message_in = [{"role": "user", "content": prompt}]
            response, info = gpt.llm_call(message_in, model, "config/key_API.json")
            tokens += info["usage"]["total_tokens"]
            task["generated_code"] = gpt.extract_code(response, "verilog")[-1]
            # step 2, classify the generated code
            if step2_algorithm:
                response = circuit_type_by_code(task["generated_code"])
            else:
                prompt = "Please classify the following verilog code into combinational circuit or sequential circuit:\n" + task["generated_code"] + "\nthe circuit description is:\n" + task["description"] + "\n IMPORTANT: please only reply one word as the response. If this verilog code is a combinational circuit, please reply 'CMB'. If this verilog code is a sequential circuit, please reply 'SEQ'. \nVERY IMPORTANT: DO NOT reply anything else."
                system_message = "You are a very smart AI, please classify the following verilog code into combinational circuit (CMB) or sequential circuit (SEQ). You already have the knowledge to do this."
                message_in = [{"role": "user", "content": prompt}]
                response, info = gpt.llm_call(message_in, model, "config/key_API.json", temperature=0.5, system_message=system_message)
                tokens += info["usage"]["total_tokens"]
            if ("CMB" in response) or ("combinational" in response):
                task["generated_circuit_type"] = "CMB"
            elif ("SEQ" in response) or ("sequential" in response):
                task["generated_circuit_type"] = "SEQ"
            else:
                task["generated_circuit_type"] = response
            consistent = task["circuit_type"] == task["generated_circuit_type"]
            unmatched += 1 if not consistent else 0
            new_msg = "[%s] %s\n" % (task["task_id"], "consistent" if consistent else "should be %s, but got %s; code:\n%s" % (task["circuit_type"], task["generated_circuit_type"], task["generated_code"]))
            txt_out += new_msg
            additional_info = "unmatched: %d\n" % (unmatched) + "total tokens: %d\n" % (tokens)
            # resave the txt every time a task is finished
            with open(save_path, 'w') as f:
                f.write(txt_out+additional_info)
            print(new_msg, end="")
        print("Circuit type generation finished! unmatched: %d; tokens: %d" % (unmatched, tokens))

    def task_gen_circuit_type_strmatch(self, save_path):
        SEQ_keywords = ["clock", "reset", "posedge", "negedge", "clk"]
        unmatched = 0
        if not ("circuit_type" in self.data[0].keys()):
            raise ValueError("circuit_type information not found!")
        for task in self.data:
            # for keyword in SEQ_keywords:
            #     if keyword in task["module_code"]:
            #         task["circuit_type_strmatch"] = "SEQ"
            #         break
            # else:
            #     task["circuit_type_strmatch"] = "CMB"
            task["circuit_type_strmatch"] = circuit_type_by_code(task["module_code"])
            if task["circuit_type_strmatch"] != task["circuit_type"]:
                print("%s: should be %s, but got %s" % (task["task_id"], task["circuit_type"], task["circuit_type_strmatch"]))
                unmatched += 1
        print("Circuit type generation finished! unmatched: %d" % (unmatched))

# this function is used to merge the data from VerilogEval (originally from HDLBits)
# we don't need to run this function every time, because the merged data is already saved in the data folder
def merge_json_from_VerlogEval(VerilogDescription_Human_path, VerilogEval_Human, output_path):
    """
    jsonl: jsonl is a json file with no limit on the size of the whole file, but each line should be smaller than 2GB

    #### VerilogDescription_Human.jsonl:
    - task_id: the name of task
    - detail_description: the description in pure text form, from HDLBits website

    #### VerilogEval_Human.jsonl:
    - task_id: the name of task
    - prompt: the module header in verilog
    - canonical_solution: the canonical verilog solution for the problem (without header). In other words, the verilog code corresponding to the problem
    - test: the golden testbench solution

    #### output - HDLBits_data.jsonl:
    - task_id: the name of task
    - task_number: the number of task (starting from 1)
    - description: detail_description from VerilogDescription_Human.jsonl
    - header: prompt from VerilogEval_Human.jsonl
    - module_code: prompt + canonical_solution from VerilogEval_Human.jsonl
    - testbench: test from VerilogEval_Human.jsonl

    """
    data_discription = load_json_lines(VerilogDescription_Human_path)
    data_eval = load_json_lines(VerilogEval_Human)
    data_merged = []
    for i in range(len(data_discription)):
        # find the corresponding line in data_eval with the same task_id
        for j in range(len(data_eval)):
            if data_discription[i]["task_id"] == data_eval[j]["task_id"]:
                break
        # merge the data
        data_merged.append({
            "task_id": data_discription[i]["task_id"],
            "task_number": i+1,
            "description": data_discription[i]["detail_description"],
            "header": data_eval[j]["prompt"],
            "module_code": data_eval[j]["prompt"] + data_eval[j]["canonical_solution"],
            "testbench": data_eval[j]["test"]
        })
    save_json_lines(data_merged, output_path)
    print("Merging finished!")

# this function is a primary function to return the module code according to task_id or task_number
# now we can use Analyzer to access the data and return the module code
def return_module_code(id_or_number, output_path=None):
    """
    - Return the module code according to task_id or task_number.
    - will return to a variable if output_path is not determined
    - otherwise, directly write it into a txt file
    """
    data = load_json_lines(MERGED_DATA_PATH)
    line = find_line_jsonl(id_or_number, data)
    # write it into txt file
    if output_path is not None:
        with open(output_path, 'w') as f:
            f.write(line["module_code"])
    else:
        return line["module_code"]
    
# def main():
#     merge_json_from_VerlogEval(VerilogDescription_Human_path, VerilogEval_Human, MERGED_DATA_PATH)

def circuit_type_by_code(code:str):
    """
    - input: code
    - output: "CMB" or "SEQ"
    """
    def string_to_words(string:str):
        words = string.split(" ")
        words = [word for word in words if word != ""]
        return words
    # _SEQ_exit_pos = 0 # for debug
    circuit_type = "CMB" # will be changed to "SEQ" if sequential
    if "always" in code:
        while True:
            always_start = code.find("always")
            if always_start == -1:
                break
            if code[always_start-1] not in [" ", "\n", "\t", ";"]:
                code = code[always_start+6:]
                continue
            elif code[always_start+6] not in [" ", "@"]:
                # check always_ff, _comb and _latch
                if code[always_start+6] == "_":
                    always_word = code[always_start:code[always_start:].find(" ")+always_start]
                    if always_word == "always_ff" or always_word == "always_latch":
                        circuit_type = "SEQ"
                        break
                code = code[always_start+6:]
                continue
            # check if there is a begin till next ";"
            next_semicolon = code[always_start:].find(";")
            if "begin" in code[always_start:always_start+next_semicolon]:
                has_begin = True
                always_end = code[always_start:].find("end") + always_start
            else:
                has_begin = False
                always_end = next_semicolon + always_start
            always_block = code[always_start:always_end]
            # currently we use a naive way to check if the always block is sequential or not; will be improved in the future
            # check if () exist for the sensitivity list
            at_pos = always_block.find("@")
            # check the first not-" " character after "@"
            char_pos = at_pos
            for char in always_block[at_pos+1:]:
                char_pos += 1
                if char != " ":
                    break
            has_bracket = True if char == "(" else False
            signal_list = []
            if has_bracket:
                sensitivity_list = always_block[always_block.find("(")+1:always_block.find(")")]
                sensitivity_list = sensitivity_list.split(",")
                for signal in sensitivity_list:
                    # get none-space words:
                    signal_seg = string_to_words(signal)
                    if len(signal_seg) > 1 and ("posedge" in signal_seg or "negedge" in signal_seg):
                        circuit_type = "SEQ"
                        # _SEQ_exit_pos = 1
                        break
                    signal_list.append(signal_seg[-1])
            else: # no bracket, always @ a begin xxx = xxx end;
                sensitivity_list_end = always_block[char_pos:].find(" ")
                sensitivity_signal = always_block[char_pos:char_pos+sensitivity_list_end]
                signal_list.append(sensitivity_signal)
            if "*" in signal_list:
                code = code[always_end:]
                continue
            if circuit_type == "SEQ":
                # _SEQ_exit_pos = 2
                break
            else:
                break_always_block = string_to_words(always_block)
                if "<=" in break_always_block:
                    circuit_type = "SEQ"
                # currently we use a naive way. Following codes are skipped
                # check_next_signal = False
                # for seg in break_always_block:
                #     if check_next_signal:
                #         if seg not in signal_list:
                #             circuit_type = "SEQ"
                #             break
                #     if "=" in seg:
                #         check_next_signal = True
                #     else:
                #         check_next_signal = False
            if circuit_type == "SEQ":
                # _SEQ_exit_pos = 3
                break
            code = code[always_end:]
    return circuit_type

if __name__ == "__main__":
    main()