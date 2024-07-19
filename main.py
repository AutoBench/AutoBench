"""
Description :   This is the head file of the project
Author      :   Ruidi Qiu (r.qiu@tum.de)
Time        :   2023/11/28 11:19:59
LastEdited  :   2024/4/27 13:00:36
"""

import loader_saver as ls
import config.config as cfg
import LLM_call as gpt
import autoline as al
import iverilog_call as iv
from config.config import CFG_CUS_PATH as CUSTOM_CFG_PATH
import getopt
import sys
import os

def main(custom_cfg_path: str = CUSTOM_CFG_PATH):
    
    my_config = cfg.load_config(custom_cfg_path)
    my_config = ls.add_save_root_to(my_config)
    if my_config.save.log.en:
        ls.save_config(my_config)
    if my_config.run.mode == "chatgpt":
        gpt.run_like_a_chatgpt(my_config)
    elif my_config.run.mode == "iverilog":
        iv.run_iverilog(my_config)
    elif my_config.run.mode == "autoline":
        al.run_autoline(my_config)
    elif my_config.run.mode == "dataset_manager":
        pass # TODO
    else:
        raise ValueError("Invalid run mode: " + my_config.run.mode)
    print("Done!\n\n")

if __name__ == "__main__":
    # we have these commands:
    # if no command, run the main function main()
    # if -h/--help, print the help message
    # if -d/--demo + name, run the main function with chosen demo config file
    # if -c/--config, run the main function with the custom config file in config/custom.yaml
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:c:", ["help", "demo=", "config="])
    except getopt.GetoptError:
        print("Invalid command")
        sys.exit(2)
    if len(opts) == 1:
        opt, arg = opts[0]
        if opt in ("-h", "--help"):
            print("Usage: python main.py [-h] [-d demo_name] [-c custom_config_path]\n\nOptions:\n  -h, --help\t\t\tShow this help message and exit\n  -d, --demo demo_name\t\tRun the main function with chosen demo config file\n  -c, --config\tRun the main function with the custom config file in config/custom.yaml\n\nIf no command, run the main function with the custom config file in config/custom.yaml\n")
            sys.exit()
        elif opt in ("-d", "--demo"):
            demo_dir = "config/demos"
            if arg in ["cmb", "CMB"]:
                main(os.path.join(demo_dir, "CMB_template.yaml"))
            elif arg in ["seq", "SEQ"]:
                main(os.path.join(demo_dir, "SEQ_template.yaml"))
            elif arg in ["156", "total"]:
                main(os.path.join(demo_dir, "156_template.yaml"))
            elif arg in ["bl", "baseline"]:
                main(os.path.join(demo_dir, "156_baseline_template.yaml"))
            else:
                print("Invalid demo name")
                sys.exit(2)
        elif opt in ("-c", "--config"):
            main(arg)
        else:
            print("Invalid command")
            sys.exit(2)
    elif len(opts) == 0:
        main()
    else:
        print("Invalid command. Only one argument is allowed. Use -h or --help for help.")
        sys.exit(2)