"""
Description :   some tool functions for prompt scripts and their stages
Author      :   AutoBench's Author (Anonymous Email)
Time        :   2024/4/25 13:26:06
LastEdited  :   2024/5/1 01:27:14
"""

import math
####################################
# used by pychecker_SEQ
def extract_signals(header):
    """
    - given the header of a module, extract the signals
    - output format: [{"name": "signal_name", "width": "[x:x]", "type": "input/output"}, ...]
    """
    def get_width_ifhave(signal):
        if len(signal) > 2 and "[" in signal[-2] and "]" in signal[-2]:
            # remove other parts except the [x:x]
            width = signal[-2]
            width = width.split("[")[1].split("]")[0]
            width = "[" + width + "]"
            return width
        else:
            return ""
    signals = header.split("(")[1].split(")")[0].split(",")
    signals = [signal.strip().split(" ") for signal in signals]
    signals = [{"name": signal[-1], "width": get_width_ifhave(signal), "type": signal[0]} for signal in signals]
    return signals

def fdisplay_code_gen(header, ckeck_en=True):
    """
    - input: head, like: 
        module top_module(
            input clk,
            input reset,
            output reg [3:0] q);
    - return:
        - no check: $fdisplay(file, "scenario: %d, clk = %d, reset = %d, q = %d", scenario, clk, reset, q);
        - check: $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, q = %d", scenario, clk, reset, q);
    """
    signals = extract_signals(header)
    begining = '$fdisplay(file, "'
    ending = ");"
    check = "[check]" if ckeck_en else ""
    middle1 = check + "scenario: %d"
    middle2 = ", scenario"
    middle1_signals = ""
    middle2_signals = ""
    for signal in signals:
        middle1_signals += ", %s = %%d" % signal["name"]
        middle2_signals += ", %s" % signal["name"]
    middle1 += middle1_signals + '"'
    middle2 += middle2_signals
    return begining + middle1 + middle2 + ending

def pychecker_SEQ_TB_standardization(code, header):
    """
    - refine the TB code
    - 1. patch the weird bug of gpt generated verilog code
    - 2. add $fdisplay in the repeat block if not exist
    - 3. split the delay to multiple #10
    - 4. add #10 in front of the second $display if there are two $display and no delay between them
    - 5. add $fdisplay in front of the second #10 if there are two #10 and no $display between them
    - 6. find all the $fdisplay sentence and rewrite them in a standard format
    """
    code = verilog_patch(code)
    code = add_fdisplay_to_repeat(code, header)
    code = split_delay_to_delays(code)
    code = find_and_rewrite_fdisplay(code, header)
    code = add_delay_into_2displays_or_scenarios(code)
    code = add_display_into_2delays(code, header)
    return code

def pychecker_CMB_TB_standardization(code, header):
    """
    different from pychecker_SEQ_TB_standardization, there is no timing issues in CMB
    """
    code = verilog_patch(code)
    code = find_and_rewrite_fdisplay(code, header)
    return code

def find_and_rewrite_fdisplay(code:str, header:str):
    """
    This function is used to find all the $fdisplay sentence and rewrite them in a standard format
    """
    fdisplay_check = fdisplay_code_gen(header, ckeck_en=True)
    fdisplay_nocheck = fdisplay_code_gen(header, ckeck_en=False)
    current_location = 0
    code_processed = ""
    code_todo = code
    start = 0
    end = 0
    while True:
        start = code_todo[current_location:].find("$fdisplay")
        if start == -1:
            break
        end = code_todo[start:].find(");") + start +1
        display_sentence = code_todo[start:end+1]
        code_processed += code_todo[:start]
        code_todo = code_todo[end+1:]
        check_en = True if "[check]" in display_sentence else False
        if check_en:
            code_processed += fdisplay_check
        else:
            code_processed += fdisplay_nocheck
    code = code_processed + code_todo
    return code

def add_fdisplay_to_repeat(code:str, header:str):
    code_done = ""
    code_todo = code
    while True:
        repeat_start = code_todo.find("repeat")
        if repeat_start == -1:
            break
        # check if no display until the next scenario
        next_scenario = code_todo[repeat_start:].find("$fdisplay") # it is ok even if it is -1
        if "[check]" not in code_todo[repeat_start:repeat_start+next_scenario]:
            fdisplay_code = fdisplay_code_gen(header, ckeck_en=True) + " "
        else:
            fdisplay_code = fdisplay_code_gen(header, ckeck_en=False) + " "
        # check if this repeat is single-line or multi-line
        new_line = min_no_minusone(code_todo[repeat_start:].find("\n"), code_todo[repeat_start:].find("//"))
        if "begin" not in code_todo[repeat_start:repeat_start+new_line]:
            # single-line repeat, add begin end
            repeat_end = new_line + repeat_start
            after_repeat = code_todo[repeat_start:repeat_start+new_line].find(")") + 2 + repeat_start
            repeat_block = code_todo[repeat_start:after_repeat] + "begin " + code_todo[after_repeat:repeat_end] + " end" 
        else:
            repeat_end = code_todo[repeat_start:].find("end") + repeat_start
            repeat_block = code_todo[repeat_start:repeat_end]
        # check if there is a $fdisplay in the repeat block
        if "$fdisplay" not in repeat_block:
            # no fdisplay, add one in front of the first delay
            delay_start = repeat_block.find("#")
            # add the fdisplay before the first delay
            code_done += code_todo[:repeat_start] + repeat_block[:delay_start] + fdisplay_code + repeat_block[delay_start:]
        else:
            code_done += code_todo[:repeat_start] + repeat_block
        code_todo = code_todo[repeat_end:]
    code_done += code_todo
    return code_done

# def add_delay_into_2displays(code):
#     """
#     - is there are two $display and there is no delay between them, add #10 at the front of the second $display
#     - two kinds of action: insert #10 into two displays; insert #10 into one display and 
#     """
#     code_todo = code
#     code_done = ""
#     while True:
#         if "$fdisplay" in code_todo:
#             # find the next $fdisplay
#             start_first = code_todo.find("$fdisplay")
#             end_first = code_todo[start_first:].find(");") + start_first + 2
#             start_second = code_todo[end_first:].find("$fdisplay") + end_first
#             if start_second == -1:
#                 break
#             # check if there is a delay between them
#             subcode = code_todo[end_first:start_second]
#             delay_exist = ("#" in subcode)
#             if (not delay_exist):
#                 code_done += code_todo[:end_first] + " #10; "
#             else:
#                 code_done += code_todo[:end_first]
#             code_todo = code_todo[end_first:]
#         else:
#             code_done += code_todo
#             break
#     return code_done

def add_delay_into_2displays_or_scenarios(code):
    """
    - is there are two $display and there is no delay between them, add #10 at the front of the second $display
    - three cases:
        - two displays: if no delay, insert
        - display and scenario: if no delay, insert
        - scenario and display: delete the delay (not sure if we should do, to be continue)
    """
    code_todo = code
    code_done = ""
    new_scenario_next = True
    while True:
        if "$fdisplay" in code_todo:
            # find the next $fdisplay or scenario
            if new_scenario_next:
                start_first = code_todo.find("scenario =")
                end_first = code_todo[start_first:].find(";") + start_first + 1
                new_scenario_next = False
                new_scenario_now = True
            else: 
                start_first = code_todo.find("$fdisplay")
                end_first = code_todo[start_first:].find(");") + start_first + 2
                new_scenario_now = False
            # check scenario
            start_scenario = code_todo[end_first:].find("scenario =" )
            start_second = code_todo[end_first:].find("$fdisplay")
            if start_second == -1:
                code_done += code_todo
                break
            if not (start_scenario == -1) and (start_scenario < start_second):
                # next is a new scenario
                start_second = start_scenario
                new_scenario_next = True
            start_second += end_first
            # check and insert delay
            subcode = code_todo[end_first:start_second]
            if new_scenario_now:
                # it is ok if there is no delay between scenario and display because delay already exists behind the last scenario
                code_done += code_todo[:end_first]
            else:
                if (not ("#" in subcode)):
                    code_done += code_todo[:end_first] + " #10; "
                else:
                    code_done += code_todo[:end_first]
            code_todo = code_todo[end_first:]
        else:
            code_done += code_todo
            break
    return code_done

def add_display_into_2delays(code:str, header:str=None):
    """if there are two #10 and there is no $fdisplay between them, add $fdisplay at the front of the second #10"""
    def find_display(code:str):
        load = ""
        check = ""
        start = code.find("$fdisplay")
        end = code[start:].find(")") + start
        first_display = code[start:end+1] + ";"
        if "[check]" in first_display:
            check = first_display
            load = check.replace("[check]", "")
        else:
            load = first_display
            check = load.replace('"scenario: ', '"[check]scenario: ')
        return load, check
    if header is None:
        load, check = find_display(code)
    else: 
        load = fdisplay_code_gen(header, ckeck_en=False)
        check = fdisplay_code_gen(header, ckeck_en=True)
    code_parts = code.split("#10")
    if len(code_parts) >= 2:
        # make sure there are at least two #10
        for idx, subcode in enumerate(code_parts[:-2]):
            real_idx = idx
            if "$fdisplay" not in subcode:
                code_parts[real_idx] += load + " "
    return "#10".join(code_parts)

def split_delay_to_delays(code:str):
    # start from the first Scenario/scenario
    start = max(code.find("scenario"), code.find("Scenario"))
    code_before = code[:start]
    code = code[start:]
    code = code.split("#")
    for idx, subcode in enumerate(code):
        if idx != 0:
            # find the delay number; i.e., "20 asdbuaw" return "20"
            digit = ""
            for char in subcode:
                if char.isdigit():
                    digit += char
                else:
                    break
            if digit and (digit != "10"):
                delay_time = int(digit)
                delay10_num = math.ceil(delay_time / 10.0)  
                # replace the original delay with multiple #10
                new_delay = "#10; " * delay10_num
                new_delay = new_delay[1:-2]
                code[idx] = new_delay + subcode[len(digit):]
    return code_before + "#".join(code)

def verilog_patch(vcode:str):
    """
    here is a patch for a weird bug of gpt generated verilog code
    the bug is "initial begin ... }" or "initial { ... }"
    """
    if r"{\n" in vcode:
        vcode = vcode.replace(r"{\n", r"begin\n")
    # scan the code line by line
    vcode_lines = vcode.split("\n")
    endmodule = False
    for i, line in enumerate(vcode_lines):
        line_temp = line.replace(" ", "")
        if line_temp == "}":
            vcode_lines[i] = line.replace("}", "end")
        if "endmodule" in line_temp:
            if endmodule:
                vcode_lines[i] = line.replace("endmodule", "")
            else:
                endmodule = True
    return "\n".join(vcode_lines)

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

class given_TB:
    def __init__(self, header) -> None:
        """
        1. initialize sim time, module testbench and signals
        2. initialize "integer file, scenario;"
        3. instantiate the DUT
        4. clock generation (if have)
        5. scenario based test
        6. endmodule
        """
        self.header = header
        self.signals = extract_signals(self.header)
        self.TB_code_head = ""
        self.TB_code_head += "`timescale 1ns / 1ps\nmodule testbench;\n"
        self.TB_code_head += self.initial_signals(self.signals) + "\n"
        self.TB_code_head += "integer file, scenario;\n"
        self.TB_code_head += "// DUT instantiation\n"
        self.TB_code_head += self.instantiate_module_by_signals("top_module", "DUT", self.signals) + "\n"
        self.TB_code_head += self.clock_generation()
        self.TB_code_head += '\ninitial begin\n    file = $fopen("TBout.txt", "w");\nend\n'
        # self.TB_code_test = '// Test scenarios\ninitial begin\n    file = $fopen("TBout.txt", "w");\n\n    // write your codes here\n\n    $fclose(file);\n    $finish;\nend\n'
        self.TB_code_test = '// Scenario Based Test\ninitial begin\n\n    // write your scenario checking codes here, according to scenario information\n\n    $fclose(file);\n    $finish;\nend\n'
        self.TB_code_tail = "\nendmodule\n"
    
    def gen_template(self):
        return self.TB_code_head + self.TB_code_test + self.TB_code_tail

    def clock_generation(self):
        clk_en = False
        for signal in self.signals:
            if signal["name"] in ["clk", "clock"]:
                clk_en = True
                clk = signal["name"]
                break
        if not clk_en:
            return ""
        else:
            return "// Clock generation\ninitial begin\n    [clk] = 0;\n    forever #5 [clk] = ~[clk];\nend\n".replace("[clk]", clk)
        
    @staticmethod
    def initial_signals(signals):
        """
        - this function is used to initialize signals
        """
        initial_str = ""
        for signal in signals:
            if signal["type"] == "input":
                initial_str += f"reg {signal['width']} {signal['name']};\n"
            else:
                initial_str += f"wire {signal['width']} {signal['name']};\n"
        return initial_str
    
    @staticmethod
    def instantiate_module_by_signals(module_name, instantiate_name, signals):
        """
        - this function is used to instantiate a module by signals
        - the signals should be like [{"name": "a", "width": "[3:0]", "type": "input"}, ...]
        """
        instantiate_str = f"{module_name} {instantiate_name} (\n"
        for signal in signals:
            if signal["width"]:
                instantiate_str += f"\t.{signal['name']}({signal['name']}),\n"
            else:
                instantiate_str += f"\t.{signal['name']}({signal['name']}),\n"
        instantiate_str = instantiate_str[:-2] + "\n);"
        return instantiate_str

# used by stage 5
def signal_dictlist_template(header:str, exclude_clk:bool=False) -> str:
    """
    for the automatic generation of signals in testbench
    target: given the DUT header, generate the signal output template
    eg: if we have a DUT header like "module DUT(input a, b, c, output d, e);", the signal output template should be like "[{"check_en": 0, "scenario": 1, "a": 1, "b": 0, "c":1, "d": 0, "e": 0}, {"check_en": 1, "scenario": 1, "a": 0, "b": 0, "c":1, "d": 0, "e": 0}]"
    """
    signals_dictlist1 = header_to_dictlist(header, exclude_clk=exclude_clk)
    signals_dictlist2 = header_to_dictlist(header, exclude_clk=exclude_clk)
    signals_dictlist3 = header_to_dictlist(header, check_en=True, exclude_clk=exclude_clk)
    signals_dictlist = signals_dictlist1 + signals_dictlist2 + signals_dictlist3
    return str(signals_dictlist)

def header_to_dictlist(header:str, value=1, scenario_idx=1, check_en = False, exclude_clk:bool=False) -> str:
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
    signals = extract_signals(header)
    if exclude_clk:
        signals = [signal for signal in signals if signal["name"] not in ["clk", "clock"]]
    dict_out = {}
    dict_list_out = [dict_out]
    dict_out["check_en"] = check_en
    dict_out["scenario"] = scenario_idx
    for signal in signals:
        dict_out[signal["name"]] = value
    return dict_list_out


def signal_dictlist_template_CMB(header:str, exclude_clk:bool=False) -> str:
    """
    for the automatic generation of signals in testbench
    target: given the DUT header, generate the signal output template
    eg: if we have a DUT header like "module DUT(input a, b, c, output d, e);", the signal output template should be like "[{"check_en": 0, "scenario": 1, "a": 1, "b": 0, "c":1, "d": 0, "e": 0}, {"check_en": 1, "scenario": 1, "a": 0, "b": 0, "c":1, "d": 0, "e": 0}]"
    """
    signals_dictlist1 = header_to_dictlist(header, exclude_clk=exclude_clk)
    
    return str(signals_dictlist1)

def header_to_dictlist_CMB(header:str, value=1, scenario_idx=1, exclude_clk:bool=False) -> str:
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
    signals = extract_signals(header)
    if exclude_clk:
        signals = [signal for signal in signals if signal["name"] not in ["clk", "clock"]]
    dict_out = {}
    dict_list_out = [dict_out]
    # dict_out["scenario"] = scenario_idx
    for signal in signals:
        dict_out[signal["name"]] = value
    return dict_list_out

def min_no_minusone(a, b):
    if a == -1:
        return b
    if b == -1:
        return a
    return min(a, b)

if __name__ == "__main__":
    header = """module top_module(
	input clk,
	input reset,
	output shift_ena);
"""

    code = """
`timescale 1ns / 1ps
module testbench;
    reg  clk;
    reg  reset;
    wire  shift_ena;

    integer file, scenario;
    // DUT instantiation
    top_module DUT (
        .clk(clk),
        .reset(reset),
        .shift_ena(shift_ena)
    );
    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        file = $fopen("TBout.txt", "w");
    end

    // Test scenarios
    initial begin
        // Scenario 1: Reset high for at least one cycle
        scenario = 1;
        reset = 1;
        $fdisplay(file, "scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #10;
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #10;
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);

        // Scenario 2: Reset low after one cycle, check for next four cycles
        scenario = 2;
        reset = 0;
        $fdisplay(file, "scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #10;
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #10;
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #10;
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #10;
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);

        // Scenario 3: Hold without reset, check for more than ten cycles
        scenario = 3;
        #10; #10; #10;
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #10; #10; #10; // Already waited 6 cycles, waiting 4 more
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);

        // Scenario 4: Reapply the reset
        scenario = 4;
        reset = 1;
        $fdisplay(file, "scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #10;
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        reset = 0;
        $fdisplay(file, "scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #10;
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);

        // Scenario 5: Toggled reset high and low within same cycle
        scenario = 5;
        reset = 1;
        $fdisplay(file, "scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #5; // Toggle within the high phase of the clock
        reset = 0;
        $fdisplay(file, "scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);
        #5; // Completing the clock cycle
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);

        // Scenario 6: constant clock with no resets
        scenario = 6;
        reset = 0;
        #10; #10; #10; // Let this run for 3 cycles
        $fdisplay(file, "[check]scenario: %d, clk = %d, reset = %d, shift_ena = %d", scenario, clk, reset, shift_ena);

        $fclose(file);
        $finish;
    end

endmodule

"""

    print(pychecker_SEQ_TB_standardization(code, header))
    