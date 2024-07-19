"""
Description :   This file is used to handle json files
Author      :   Ruidi Qiu (r.qiu@tum.de)
Time        :   2023/11/19 21:49:11
LastEdited  :   
"""

import json

PROMPT_JSON = "preliminary_EXP/7420/prompt.json"
OUTPUT_TXT = "generated_prompt.txt"

"""
prompt.json template:
{
    "description" : "The 7400-series integrated circuits are a series of digital chips with a few gates each. The 7420 is a chip with two 4-input NAND gates.    Create a module with the same functionality as the 7420 chip. It has 8 inputs and 2 outputs.",
    "headmodule" : "module top_module (\ninput p1a, p1b, p1c, p1d,\noutput p1y,\ninput p2a, p2b, p2c, p2d,\noutput p2y );\nendmodule",
    "tb_property" : {"composition" : "this module is composed of 2 4-input NAND gates", "test case 1" : "NAND gate will output 1 if all inputs are 0, otherwise it will output 0"},
    "rules" : ["Attention! you should print a message after each test case. The message should contain 'the explanation of your test case' and 'error source'", "Attention! Your test cases should be as exhaustive as possible.", "your response should only contain the code"]
}
"""
def json_read(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def txt_write(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

def prompt_gen_from_jsonprompt(json_data):
    prompt_header = "You are the strongest AI agent I have ever met. You can perfect handle the job I give you. please generate a verilog testbench to test the verilog code of the design under test (DUT).\n"
    prompt_description = "The description for the DUT is: '%s'\n" % (json_data["description"])
    prompt_headmodule = "The input and output interface of this verilog code is: \n%s\n" % (json_data["headmodule"])
    prompt_rules = "The rules for this task are:\n"
    for rule in json_data["rules"]:
        prompt_rules += "    %s\n" % (rule)
    prompt_property = "to help you better generate the testbench for the DUT, we will give you some tips that you should consider when generating the testbench.\n"
    prompt_property += "The composition of the DUT is '%s'\n" % (json_data["tb_property"]["composition"])
    for key in json_data["tb_property"].keys():
        if key != "composition":
            prompt_property += "    %s: %s\n" % (key, json_data["tb_property"][key])
    prompt = prompt_header + prompt_description + prompt_headmodule + prompt_rules + prompt_property
    return prompt

def main():
    json_file = PROMPT_JSON
    output_txt = OUTPUT_TXT
    json_data = json_read(json_file)
    prompt = prompt_gen_from_jsonprompt(json_data)
    txt_write(output_txt, prompt)

if __name__ == "__main__":
    main()