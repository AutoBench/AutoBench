"""
Description :   This module contains all functions related to loading and saving (except config loading). This file is copied and modified from OplixNet project.
Author      :   AutoBench's Author (Anonymous Email)
Time        :   2023/11/28 14:03:56
LastEdited  :   2024/4/17 22:09:35
"""

import os
from config.config import Dict
import config.config as cfg
# import matplotlib.pyplot as plt
import yaml
import json
from utils.utils import print_time, Timer, str_list

########################## yaml/json utils ############################
def load_yaml_dict(path: str):
    with open(path, 'rb') as f:
        yaml_dict = yaml.safe_load(f)
    return yaml_dict

def load_json_dict(path: str):
    with open(path, 'r') as f:
        json_dict = json.load(f)
    return json_dict

def save_dict_json_form(json_dict, path: str):
    with open(path, 'w') as f:
        json.dump(json_dict, f, indent=4)

def load_txt(path: str):
    with open(path, 'r') as f:
        txt = f.read()
    return txt

# jsonl related:
def load_json_lines(path: str):
    with open(path, 'r') as f:
        data = [json.loads(line) for line in f]
    return data

def save_json_lines(data, path: str):
    with open(path, 'w') as f:
        for line in data:
            json.dump(line, f)
            f.write('\n')

def find_line_jsonl(id_or_number, data):
    """
    quickly find the line in data by task_id or task_number
    """
    if isinstance(id_or_number, str):
        for line in data:
            if line["task_id"] == id_or_number:
                return line
    elif isinstance(id_or_number, int):
        for line in data:
            if line["task_number"] == id_or_number:
                return line

########################## set save path ############################
def save_path_setting(config, save_type, custom_name=''):
    '''support log/data/plot/postproc saving'''
    SAVE_TYPE_DICT = {
        'log': config.save.log,
        'message': config.save.message,
        'tb': config.save.iverilog,
        'dir': config.save.pub
    }
    type_config = SAVE_TYPE_DICT[save_type]
    run = config.run
    pub = config.save.pub
    if not save_type in SAVE_TYPE_DICT.keys():
        raise Exception('no such saving type named \"%s\"' % (save_type))
    # file name:
    if pub.prefix is None:
        unique_name = '%s'%(run.time)
    else:
        unique_name = '%s_%s'%(str(pub.prefix), run.time)
    if custom_name != '':
        custom_name = '%s_'%(custom_name)
    file_name = custom_name + unique_name
    # dir:
    # if (pub.dir is None):
    #     save_dir = type_config.dir
    # else:
    #     if pub.subdir not in ['', None] and not pub.subdir.endswith('/'): # in case of missing '/'
    #         pub.subdir = pub.subdir+'/'
    #     else:
    #         pub.subdir = pub.subdir 
    #     save_dir = '%s%s%s/'%(pub.dir, pub.subdir, unique_name)
    if pub.subdir not in ['', None] and not pub.subdir.endswith('/'): # in case of missing '/'
        pub.subdir = pub.subdir+'/'
    else:
        pub.subdir = pub.subdir 
    save_dir = '%s%s%s/'%(pub.dir, pub.subdir, unique_name)
    if save_type == 'dir':
        return save_dir
    if os.path.exists(save_dir) != True: #dir check
        os.makedirs(save_dir)
    # suffix:
    suffix_dict = {'log': '.log', 'tb': '.v'}#, 'model': '.pt'}
    if save_type == 'message': # leave the suffix to the user
        suffix = ''
    else:
        suffix = suffix_dict[save_type]
    # merge:
    save_path = save_dir + file_name + suffix
    return save_path
    
def add_save_root_to(config):
    """save root; ends with '/'"""
    config.save.root = save_path_setting(config, 'dir')
    return config

############################# log save ###############################
def print_dict(file, input_dict, indent='', ind_style=' '):
    if isinstance(input_dict, Dict) or isinstance(input_dict, dict):
        dict_items = input_dict.items()
    else:
        raise TypeError("input type of func 'print_dict' is not Dict(obj) or dict")
    for k, v in dict_items:
        if not isinstance(v, Dict) and not isinstance(v, dict):
            file.write('%s%s: %s\n' % (indent, k, v))
        else:
            file.write('%s%s: \n' % (indent, k))
            next_indent = '%s   %s'%(ind_style, indent)
            print_dict(file, v, next_indent, ind_style)

def print_config(file, config):
    """
    split mode: `running info` + `custom` config + `default` config
    iwantall mode: `custom` config + `merged` config + `default` config
    merge mode: `merged` config
    """
    mode = config.save.log.cfg_pmode
    indent_style = ' '
    if mode == 'split':
        # running information: (only split mode)
        file.write('---------------running info---------------\n')
        file.write('last version: %s\n' % (config.run.version))
        file.write('custom config file: %s\n' % (config.run.custom_path))
        file.write('starting time: %s\n' % (config.run.time))
        file.write('host name: %s\n' % (config.run.hostname))
        file.write('process ID: %s\n' % (config.run.pid))
        file.write('------------------------------------------\n')
    if mode in ['split', 'iwantall']:
        # custom config:
        custom_cfg, default_cfg = cfg.load_split_config(custom_config_path=config.run.custom_path)
        file.write('\n---------------custom config--------------\n')
        if custom_cfg is None:
            file.write('\nNo customized configuration\n')
        else:
            print_dict(file, custom_cfg, ind_style = indent_style)
        file.write('------------------------------------------\n')
    if mode in ['merge', 'iwantall']:
        # merged config:
        file.write('------config info (custom + default)------\n')
        print_dict(file, config, ind_style = indent_style)
        file.write('------------------------------------------\n')
    if mode in ['split', 'iwantall']:
        # default config:
        file.write('\n--------------default config--------------\n')
        print_dict(file, default_cfg, ind_style = indent_style)
        file.write('------------------------------------------\n')

def save_config(config):
    save_path = save_path_setting(config, 'log')
    with open(save_path, 'a') as file:
        #notes:
        if not config.save.log.notes is None:
            file.write('%s\n\n' % (config.save.log.notes))
        #config information:
        print_config(file, config)

def save_log_line(line, config):
    if config.save.log.en:
        save_path = save_path_setting(config, 'log')
        with open(save_path, 'a') as file:
            file.write('%s\n'%(line))

def print_and_save(line, config):
    # print(line if not line.startswith('\n') else line[1:]) # the same format as save_log_line
    # print(line)
    # save_log_line(line, config)
    print(line)
    if config.save.log.en:
        save_log_line(line, config)

############################# message/code save #############################
def save_messages_to_txt(messages, save_path):
    with open(save_path, 'a') as file:
        for message in messages:
            if "time" in message.keys():
                file.write('########## %s (%ss used) ##########\n%s\n\n' % (message['role'], message['time'], message['content']))
            else:
                file.write('########## %s ##########\n%s\n\n' % (message['role'], message['content']))
        file.write('\n')

def print_messages(messages):
    # just like save_messages_to_txt
    for message in messages:
        if "time" in message.keys():
            print('########## %s (%ss used) ##########\n%s\n' % (message['role'], message['time'], message['content']))
        else:
            print('########## %s ##########\n%s\n' % (message['role'], message['content']))

def save_messages_to_log(messages, config):
    save_path = save_path_setting(config, 'log')
    save_messages_to_txt(messages, save_path)

def gpt_message_individual_save(messages, config, file_name = None, file_format = "json", silent = False):
    save_path = save_path_setting(config, 'message')
    # change the file name (xxx/xx.json->xxx/file_name.json)
    if file_name is not None:
        save_path = save_path.split('/')
        save_path[-1] = file_name + "." + file_format
        save_path = '/'.join(save_path)    
    if file_format == 'txt':
        save_messages_to_txt(messages, save_path)
    elif file_format == 'json':
        save_dict_json_form(messages, save_path)
    # print
    if not silent:
        print("\n")
        if file_name is not None:
            print("(file name: %s)"%(file_name))
        print('your conversation with ChatGPT has been successfully saved to "%s"\n' % (save_path))


# will be discarded in the future
def save_code_iv(code_txt, task_id, code_type, config, iverilog_dir = None, silent = False):
    """
    save the verilog TB/DUT code to a .v file. This func is for iverilog call.
    #### input:
    - code_txt: the verilog code in string format
    - task_id: the task id of the problem
    - code_type: 'TB' or 'DUT'
    - config: the config object
    - iverilog_dir: the directory to save the code. If None, use the default directory.
    """
    assert code_type in ["TB", "DUT"], "code_type should be 'TB' or 'DUT'"
    suffix_dict = {'TB': '_tb.v', 'DUT': '.v'}
    if iverilog_dir is None:
        iverilog_subdir = config.save.iverilog.subdir
        save_path = save_path_setting(config, 'tb')
        save_path = save_path.split('/')
        # insert iverilog dir
        save_path.insert(-1, iverilog_subdir)
    else:
        if not iverilog_dir.endswith('/'):
            iverilog_dir += '/'
        iverilog_path = iverilog_dir  + "name.v"
        save_path = iverilog_path.split('/')
    code_name = task_id + suffix_dict[code_type]
    save_path[-1] = code_name
    save_dir = '/'.join(save_path[:-1]) + '/'
    save_path = '/'.join(save_path)
    os.makedirs(save_dir, exist_ok=True)
    with open(save_path, 'a') as file:
        file.write(code_txt)
    if not silent:
        print("\n")
        print('your %s code has been successfully saved to "%s"\n' % (code_type, save_path))
    return {'name': code_name, 'dir': save_dir, 'path': save_path, 'code_type': code_type}

def save_code(code, path):
    with open(path, 'w') as file:
        file.write(code)

############################# __main__ ################################
if __name__ == "__main__":
    None