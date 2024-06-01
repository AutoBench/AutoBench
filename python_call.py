"""
Description :   this is used in pychecker workflow
Author      :   AutoBench's Author (Anonymous Email)
Time        :   2024/3/31 14:05:50
LastEdited  :   2024/4/28 11:19:28
"""

import os
import sys
from utils.utils import run_in_dir
from subproc import subproc_call

PYPATH = "saves_inEDA/0420~0426/MILE_STONE_DATA/pychecker_SEQ_test5_SEQ15_20240425_142931/countbcd/debug_6 copy/countbcd_tb.py"

def python_call(pypath, silent = False, timeout = 120):
    """ 
    #### input:
    - pypath: the path of the python file
    - silent: whether to print

    #### output:
    return a list of 3 elements:
    - [0] (pass or not):    bool, whether the simulation is successful
    - [1] (run_info):      dict, the iverilog compiling result {"out": out_reg, "err": err_reg, "haserror": error_exist}
    - [2]/[-1] (error_msg): str, the error message if there is any error; This is for convenience, the error message is also included in [2] or [4]

    #### functionality:
    given the path of python file, run it in the local dir.
    """
    def s_print(*args, **kwargs):
        if not silent:
            print(*args, **kwargs)
    dir = os.path.dirname(pypath)
    filename = os.path.basename(pypath)
    cmd = "python3 %s"%(filename) 
    with run_in_dir(dir):
        run_info = subproc_call(cmd, timeout) # {"out": out_reg, "err": err_reg, "haserror": error_exist}
    if run_info["haserror"]:
        s_print("python compiling failed")
        return [False, run_info, run_info["err"]]
    else:
        s_print("python compiling passed")
        return [True, run_info, ""]

def save_py_runinfo(py_run_result, dir):
    """
    save the run info of iverilog to dir
    """
    if not dir.endswith("/"):
        dir += "/"
    run_info_path = dir + "run_info_py.txt"
    lines = ""
    if py_run_result[0]:
        lines += "python compilation passed!\n\n"
    else:
        lines += "python compilation failed!\n\n"
    # output and error of cmd:
    lines += "###output:\n%s\n\n" % (py_run_result[1]["out"])
    lines += "###error:\n%s\n\n" % (py_run_result[1]["err"])
    # save to file:
    with open(run_info_path, "w") as f:
        f.write(lines)

def python_call_and_save(pypath, silent = False, timeout = 120):
    """
    run the python file and save the run info
    """
    py_run_result = python_call(pypath, silent, timeout)
    save_py_runinfo(py_run_result, os.path.dirname(pypath))
    return py_run_result

if __name__ == "__main__":
    python_call_and_save(PYPATH, silent = False)