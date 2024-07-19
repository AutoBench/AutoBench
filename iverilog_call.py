"""
Description :   This file is related to iverilog calling. Some codes are modified from autosim.py v0.2 by Rain Bellinsky.
Author      :   Ruidi Qiu (r.qiu@tum.de)
Time        :   2023/12/9 23:22:51
LastEdited  :   2024/4/29 12:51:22
"""

import os
import sys
from utils.utils import run_in_dir
from subproc import subproc_call

if os.name == 'nt':
    IC = '\\' # IC: Iterval Character
else:
    IC = '/'

RUN_DIR = "ipynb_demo/verilog_test/"

def iverilog_call(dir, silent = False, timeout = 120):
    """
    #### input:
    - dir: the name of the directory that contains all verilog files; can end with or without "/"
    - task_id: the name of the task, will be used as the name of the vvp file

    #### output:
    return a list of 5 elements:
    - [0] (pass or not):    bool, whether the simulation is successful
    - [1] (cmd1):           str, the iverilog compiling command
    - [2] (run1_info):      dict, the iverilog compiling result {"out": out_reg, "err": err_reg, "haserror": error_exist}
    - [3] (cmd2):           str, the vvp running command
    - [4] (run2_info):      dict, the vvp running result {"out": out_reg, "err": err_reg, "haserror": error_exist}
    - [5]/[-1] (error_msg): str, the error message if there is any error; This is for convenience, the error message is also included in [2] or [4]

    #### functionality:
    given the name of the directory that contains all verilog files, create a vvp file and run it.

    #### iverilog command explanation:
    - -o + file_path: output file name (.vvp's name)
    - -c + list_file_path: read file list from file
    """
    def s_print(*args, **kwargs):
        if not silent:
            print(*args, **kwargs)

    if not dir.endswith(IC):
        dir += IC
    vlist_data = vList_gen(dir)["data"]
    vlist_str = "".join(vlist_data).replace("\n", " ") # eg: saves/1204~1210/test/Mux256to1v/Mux256to1v.v saves/1204~1210/test/Mux256to1v/Mux256to1v_tb.v
    # vvp_filename = "%s.vvp"%(task_id)
    vvp_filename = "run.vvp"
    # cmd1 = "iverilog -g2012 -o %s %s"%(vvp_filename, vlist_str) # used to be vvp_path
    cmd1 = "~/bin/bin/iverilog -g2012 -o %s %s"%(vvp_filename, vlist_str) # used to be vvp_path
    s_print(cmd1)
    with run_in_dir(dir):
        run1_info = subproc_call(cmd1, timeout) # {"out": out_reg, "err": err_reg, "haserror": error_exist}
    if run1_info["haserror"]:
        s_print("iverilog compiling failed")
        return [False, cmd1, run1_info, None, None, run1_info["err"]]
    cmd2 = "~/bin/bin/vvp %s"%(vvp_filename) # used to be vvp_path
    s_print(cmd2)
    with run_in_dir(dir):
        run2_info = subproc_call(cmd2, timeout)
    if run2_info["haserror"]:
        s_print("vvp failed")
        return [False, cmd1, run1_info, cmd2, run2_info, run2_info["err"]]
    return [True, cmd1, run1_info, cmd2, run2_info, '']

def save_iv_runinfo(ivrun_info, dir):
    """
    save the run info of iverilog to dir
    """
    run_info_path = dir + "run_info.txt"
    lines = ""
    if ivrun_info[0]:
        lines += "iverilog simulation passed!\n\n"
    else:
        lines += "iverilog simulation failed!\n\n"
    # cmd 1:
    if ivrun_info[1] is not None:
        lines += "iverilog cmd 1:\n%s\n" % (ivrun_info[1])
    # output and error of cmd 1:
    if ivrun_info[2] is not None:
        lines += "iverilog cmd 1 output:\n%s\n" % (ivrun_info[2]["out"])
        lines += "iverilog cmd 1 error:\n%s\n" % (ivrun_info[2]["err"])
    # cmd 2:
    if ivrun_info[3] is not None:
        lines += "iverilog cmd 2:\n%s\n" % (ivrun_info[3])
    # output and error of cmd 2:
    if ivrun_info[4] is not None:
        lines += "iverilog cmd 2 output:\n%s\n" % (ivrun_info[4]["out"])
        lines += "iverilog cmd 2 error:\n%s\n" % (ivrun_info[4]["err"])
    # save to file:
    with open(run_info_path, "w") as f:
        f.write(lines)

def iverilog_call_and_save(dir, silent = False, timeout = 120):
    """
    run the iverilog and save the run info
    """
    iv_run_result = iverilog_call(dir, silent, timeout)
    save_iv_runinfo(iv_run_result, dir)
    return iv_run_result

def getVerilog(dir):
    """
    dir: directory to search
    """
    v_list = []
    for root, dirs, files in os.walk(dir):
        for name in files:
            # if name[-2 : ] == ".v" and "_tb" not in name:
            if name[-2 : ] == ".v":
                # v_list.append(str(root) + str(name) + '\n')
                v_list.append(str(name) + '\n')
    return v_list

def vList_gen(dir):
    """
    dir: directory to search, will save the list file in this dir
    """
    # called by iverilog_call in new dir
    file_path = "%svlist.txt"%(dir)
    filelist = getVerilog(dir) #get all .v files in dir
    with open(file_path, "w") as f:
        f.writelines(filelist)
    return {"path": file_path, "data": filelist}

def run_iverilog(config):
    """
    for main.py to directly call.
    """
    iverilog_call(config.iverilog.dir)

def main(dir=None):
    """
    directly run this file: to run iverilog
    """
    if dir is None:
        dir = input("Please enter project name (dir name):\n>> ")
    # if task_id is None:
    #     task_id = input("Please enter task_id:\n>> ")
    msg = iverilog_call(dir)
    save_iv_runinfo(msg, dir)
    print(msg)

if __name__ == '__main__':
    arg = len(sys.argv)
    if arg == 2:
        main(sys.argv[1])
    else:
        dir_path = RUN_DIR if RUN_DIR.endswith(IC) else RUN_DIR + IC
        main(RUN_DIR)
