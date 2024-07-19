"""
Description :   This is the config module of the project. This file is copied and modified from OplixNet project.
Author      :   Ruidi Qiu (r.qiu@tum.de)
Time        :   2023/11/28 11:20:33
LastEdited  :   2024/4/27 12:43:34
"""
from datetime import datetime
import yaml
import json
import os
import socket
import sys
sys.path.append("..")

CONFIG_FORMAT = "yaml" # "yaml" or "json"

# path:
DIR_PATH = 'config' # to ONN
CFG_DEF_NAME = 'default' + "." + CONFIG_FORMAT
CFG_DEF_PATH = '%s/%s' % (DIR_PATH, CFG_DEF_NAME)
CFG_CUS_NAME = 'custom' + "." + CONFIG_FORMAT
CFG_CUS_PATH = '%s/%s' % (DIR_PATH, CFG_CUS_NAME)

# discarded on 2024/2/1 23:16:25
# GPT_MODELS = {
#     "3.5" : "gpt-3.5-turbo-1106",
#     "4" : "gpt-4-1106-preview"
# }

GPT_MODELS = {
    "4t" : "gpt-4-turbo-2024-04-09",
    "3.5" : "gpt-3.5-turbo-0125",
    "4" : "gpt-4-0125-preview",
    "3.5old" : "gpt-3.5-turbo-1106",
    "4old" : "gpt-4-1106-preview"
}

CLAUDE_MODELS = {
    "opus":"claude-3-opus-20240229",
    "sonnet": "claude-3-sonnet-20240229",
    "haiku": "claude-3-haiku-20240307",
    "claude3_opus":"claude-3-opus-20240229",
    "claude3_sonnet": "claude-3-sonnet-20240229",
    "claude3_haiku": "claude-3-haiku-20240307",
    "claude2.1": "claude-2.1",
    "claude2.0": "claude-2.0",
    "claude2": "claude-2.0"
}

LLM_MODEL_REDIRECTION = {
    '4t' : GPT_MODELS["4t"],
    '3.5' : GPT_MODELS["3.5"],
    3.5 : GPT_MODELS["3.5"],
    '4' : GPT_MODELS["4"],
    '4.0' : GPT_MODELS["4"],
    4 : GPT_MODELS["4"],
    "3.5old" : GPT_MODELS["3.5old"],
    "4old" : GPT_MODELS["4old"]
}

LLM_MODEL_REDIRECTION = {**LLM_MODEL_REDIRECTION, **CLAUDE_MODELS}

######################################## utils ###########################################
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise TypeError('Boolean value expected.')

def get_time():
    now = datetime.now()
    time_str = now.strftime("%Y%m%d_%H%M%S")
    return time_str

def get_runinfo():
    hostname = socket.gethostname(),
    pid = os.getpid(),
    return hostname[0], pid[0]

################################ agparser (for future) ###################################
################################## load .yaml/.json config #####################################
def load_yaml_dict(path: str):
    with open(path, 'rb') as f:
        yaml_dict = yaml.safe_load(f)
    return yaml_dict

def load_json_dict(path: str):
    with open(path, 'r') as f:
        json_dict = json.load(f)
    return json_dict

def merge_config_dict(old_dict: dict, new_dict):
    merge_dict = {}
    if new_dict is None:
        return old_dict
    keys_old = old_dict.keys()
    keys_new = new_dict.keys()
    # we ignore the case when a key exists in new_dict but not in old_dict, because that is forbidden in my design
    # but raising an error is still needed
    for key in keys_new:
        if  key not in keys_old:
            raise Exception("%s is in custom_config but not in default_config, which is forbidden. Please modify related tree structure or add it to %s"%(key, CFG_DEF_PATH))
    for key in keys_old:
        if key not in keys_new:
            merge_dict[key] = old_dict[key]
        else:
            if isinstance(old_dict[key], dict): # if the value is a dict
                if not isinstance(new_dict[key], dict):
                    raise TypeError("value of %s isn't a dict in custom_config but is a dict in default_config"%(key))
                else:
                    merge_dict[key] = merge_config_dict(old_dict[key], new_dict[key])
            else: #if the value is not a dict:
                if isinstance(new_dict[key], dict):
                    raise TypeError("value of %s is a dict in custom_config but isn't a dict in default_config"%(key))
                else:
                    if new_dict[key] is None:
                        merge_dict[key] = old_dict[key]
                    else:
                        merge_dict[key] = new_dict[key]
    return merge_dict

def load_config_dict(mode='merge', config_old_path = CFG_DEF_PATH, config_new_path = CFG_CUS_PATH, config_format = CONFIG_FORMAT):
    if config_format == "yaml":
        load_config_func = load_yaml_dict
    elif config_format == "json":
        load_config_func = load_json_dict
    else:
        raise Exception("wrong config format input: %s (can only be yaml or json)"%(config_format))
    config_old = load_config_func(config_old_path)
    config_new = load_config_func(config_new_path)
    if mode == "merge":
        return merge_config_dict(config_old, config_new)
    elif mode == "split":
        return config_new, config_old
    else:
        raise Exception("wrong mode input: %s"%(mode))

################################### dict to object ######################################
class Dict(dict):
    """a class generated from python dict class"""
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__

    def get_copy(self):
        internal_dict = DictTodict(self)
        return dictToObj(internal_dict)
        

def dictToObj(dictObj):
    if not isinstance(dictObj, dict):
        raise TypeError("this variable is not a instance of 'dict' type")
    d = Dict()
    for k, v in dictObj.items():
        d[k] = recur_dictToObj(v)
    return d

def recur_dictToObj(dictObj):
    if not isinstance(dictObj, dict):
        return dictObj
    d = Dict()
    for k, v in dictObj.items():
        d[k] = recur_dictToObj(v)
    return d

def DictTodict(Dict_obj):
    if not isinstance(Dict_obj, Dict):
        raise TypeError("this variable is not a instance of 'Dict' type")
    d = dict()
    # recursive the Dict attr
    for k, v in Dict_obj.items():
        d[k] = recur_DictTodict(v)
    return d

def recur_DictTodict(Dict_obj):
    if not isinstance(Dict_obj, Dict):
        return Dict_obj
    d = dict()
    for k, v in Dict_obj.items():
        d[k] = recur_DictTodict(v)
    return d

def load_config_obj(custom_config_path):
    return dictToObj(load_config_dict(config_new_path = custom_config_path))

################################# config validation #####################################
def config_val(config_obj):
    # run_mode_val = ['normal', 'postproc', 'para', 'sensprune', 'custom']
    # cvnn_dinmode_val = [] # has val func in ComplexNN
    # assert config_obj.run.mode in run_mode_val, "There is no run mode named %s, only names in %s are valid"%(config_obj.run.mode, str_list(run_mode_val))
    return True

####################################### get config ######################################
def load_config(custom_config_path)->Dict: #str = CFG_CUS_PATH):
    time = get_time()
    hostname, pid =  get_runinfo()
    config = load_config_obj(custom_config_path)
    config.run.custom_path = custom_config_path
    config.run.time = time
    config.run.hostname = hostname
    config.run.pid = pid
    if not config.save.en:
        # config.save.log.en = False
        # config.save.message.en = False
        # iterate the attr of config.save, if they have en attr, set it to False
        for attr in DictTodict(config.save).keys():
            sub_config = getattr(config.save, attr)
            if isinstance(sub_config, Dict):
                try: # will raise keyerror if sub_config doesn't have en attr (it will only return false when come across AttributeError, but Dict doesn't have en attr, so it will raise KeyError)
                    hasattr(sub_config, "en")
                except:
                    continue
                setattr(sub_config, "en", False)
    if config.gpt.model in LLM_MODEL_REDIRECTION.keys():
        config.gpt.model = LLM_MODEL_REDIRECTION[config.gpt.model]
    # config_val(config)
    return config

def load_split_config(custom_config_path = CFG_CUS_PATH, default_config_path = CFG_DEF_PATH):
    # no validation. only for printing
    (custom_cfg_dict, default_cfg_dict) = load_config_dict('split', default_config_path, custom_config_path)
    if custom_cfg_dict is None:
        # custom_config can be None
        custom_cfg = None
    else:
        custom_cfg = dictToObj(custom_cfg_dict)
    default_cfg = dictToObj(default_cfg_dict)
    return custom_cfg, default_cfg

### test ###
if __name__ == "__main__":
    my_dict = {"en":{
        "a" : 1,
        "b" : {
            "en" : True,
            "d" : 3
        },
        "c" : {
            "en" : False,
            "e" : 5
        },
        "d" : {
            "f" : 6
        }
    }}
    my_dict_obj = dictToObj(my_dict)
    for attr in DictTodict(my_dict_obj.en).keys(): 
        print(attr)   
        if isinstance(getattr(my_dict_obj.en, attr), Dict):
            try:
                hasattr(getattr(my_dict_obj.en, attr), "en")
            except:
                continue    
            setattr(getattr(my_dict_obj.en, attr), "en", False)
    print(DictTodict(my_dict_obj))
    # if hasattr(my_dict_obj.en, "d"):
    #     print("yes")
    # else:
    #     print("no")