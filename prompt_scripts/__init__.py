"""
Description :   description
Author      :   AutoBench's Author (Anonymous Email)
Time        :   2024/3/23 11:30:00
LastEdited  :   2024/5/1 11:59:59
"""

from .base_script import BaseScript, BaseScriptStage
from .script_pychecker import WF_pychecker
from .script_directgen import WF_directgen

SCRIPTS_SELECTER = {
    "pychecker": WF_pychecker,
    "directgen": WF_directgen,
}

def get_script(script_name:str) -> BaseScript:
    if script_name in SCRIPTS_SELECTER:
        return SCRIPTS_SELECTER[script_name]
    else:
        raise ValueError(f"script name {script_name} is not supported")