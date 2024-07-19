"""
Description :   This file is related to auto subprocess running
Author      :   Ruidi Qiu (r.qiu@tum.de)
Time        :   2023/12/11 14:06:27
LastEdited  :   2024/4/28 13:26:18
"""

import subprocess as sp

def subproc_call(cmd, timeout=120):
    """ 
    run a cmd in shell and return the output and error
    #### input:
    - cmd: str
    - timeout: int, seconds
    #### output:
    - {"out": out_reg, "err": err_reg, "haserror": error_exist}
        - out_reg: str, output of cmd
        - err_reg: str, error of cmd
        - error_exist: int, 0 if no error, 1 if error
    
    cmd can at most run 2 minutes and if it exceeds, will return {"out": "timeout", "err": "program is timeout", "haserror": 1}
    """
    # p = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    # out, err = p.communicate()
    # error_exist = p.returncode
    # out_reg = out.decode("utf-8")
    # err_reg = err.decode("utf-8")
    timeouterror = "program is timeout (time > %ds). please check your code. Hints: there might be some infinite loop, please check all the loops in your programm. If it is a verilog code, please check if there is a $finish in the code."%(timeout)
    p = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    out_reg = ""
    err_reg = ""
    error_exist = 0
    try:
        out, err = p.communicate(timeout=timeout)
        out_reg = out.decode("utf-8")
        err_reg = err.decode("utf-8")
        error_exist = p.returncode
    except sp.TimeoutExpired:
        p.kill()
        out_reg = ""
        err_reg = timeouterror
        error_exist = 1
    return {"out": out_reg, "err": err_reg, "haserror": error_exist}

