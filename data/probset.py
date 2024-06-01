"""
Description :   the class to manage the problem set data
Author      :   AutoBench's Author (Anonymous Email)
Time        :   2024/3/6 14:01:22
LastEdited  :   2024/5/21 23:11:39
"""

if __name__ == "__main__":
    import sys
    sys.path.append(".") # add the root folder to the python path
from copy import deepcopy
import loader_saver as ls

def main():
    # test the class
    HDLBITS_DATA_PATH = "data/HDLBits/HDLBits_data.jsonl"
    CIRCUIT_TYPE_PATH = "data/HDLBits/HDLBits_circuit_type.jsonl"
    probset = HDLBitsProbset(HDLBITS_DATA_PATH, circuit_type_path=CIRCUIT_TYPE_PATH, only_tasks=["rule110"])
    print(probset.num)
    print(probset.data[0])

class dictlist:
    """
    - a class to manage the list of dict
    - form:

    {
        id_key: "xxx", #the key to identify the dict
        content1: xxx,
        content2: xxx,
        ...
    }
    """
    def __init__(self, id_key:str, path:str=None, moreinfo_path_list:list=[], only:list=None, exclude:list=[], filter:dict={}):
        self.id_key = id_key
        if path is not None:
            try:
                self.data = ls.load_json_lines(path)
            except:
                self.data = ls.load_json_dict(path)
            if moreinfo_path_list != []:
                try:
                    moreinfo = [ls.load_json_lines(moreinfo_path) for moreinfo_path in moreinfo_path_list]
                except:
                    moreinfo = [ls.load_json_dict(moreinfo_path) for moreinfo_path in moreinfo_path_list]
                for info in moreinfo:
                    self.merge(info)
            self.filter(filter)
            self.del_items(only, del_by_list=False)
            self.del_items(exclude)
        else:
            self.data = []

    @property
    def num(self):
        return len(self.data)
        
    def data_clean(self, only=None, exclude=[], filter={}):
        self.del_items(only, del_by_list=False)
        self.del_items(exclude)
        self.filter(filter)

    def find_data_by_id(self, id):
        for prob_data in self.data:
            if prob_data[self.id_key] == id:
                return prob_data
        raise ValueError("Cannot find the problem infomation with %s: "%(self.id_key) + id + ".")

    def merge(self, additional_data):
        """merge additional data into the original data"""
        for data in self.data:
            for add_data in additional_data:
                if data[self.id_key] == add_data[self.id_key]:
                    for key, value in add_data.items():
                        if key != self.id_key:
                            data[key] = value

    def filter(self, filter_dict, del_en=True):
        """
        #### Function
        - filtering the data by the key and value.
        - only the data that has the key and value will remain
        - the output will always be the filtered data, but I recommend to directly use `self.data` to get the filtered data if del_en is True
        #### Input
        - filter_dict: dict; the key and value to filter the data
        - del_en: bool; if True, the data that doesn't have the key and value will be deleted from the data. If False, the data will not change but output the filtered data
        """
        if del_en:
            for key, value in filter_dict.items():
                self.data = [prob_data for prob_data in self.data if prob_data.get(key) == value]
        else:
            filtered_data = deepcopy(self.data)
            for key, value in filter_dict.items():
                filtered_data = [prob_data for prob_data in filtered_data if prob_data.get(key) == value]
            return filtered_data

    def del_items(self, id_list, del_by_list=True):
        """
        - id_list: list of ids
        - del_by_list: bool; if True, data having the task_id in the list will be deleted. If False, the data that doesn't have the task_id in the list will be deleted
        """
        # avoid default list = [] and del_by_list = False to del all the data
        if id_list is not None and id_list != []:
            if del_by_list:
                self.data = [prob_data for prob_data in self.data if prob_data[self.id_key] not in id_list]
            else: # del the data that doesn't have the task_id in the list
                self.data = [prob_data for prob_data in self.data if prob_data[self.id_key] in id_list]

class muti_dictlist:
    """
    - mutiple dictlists, can perform the same operation on all the dictlists
    - self.dictlists: a list of dictlist
    """
    def __init__(self, id_key:str, path_list:list=None, moreinfo_path_list:list=[], only:list=None, exclude:list=[], filter:dict={}):
        """
        you can only determing the id_key (mostly, "task_id"); the dictlists can be added later
        """
        self.dictlists = []
        self.id_key = id_key
        if path_list is not None:
            self.load_dictlists(id_key, path_list, moreinfo_path_list, only, exclude, filter)

    def load_dictlists(self, id_key, path_list, moreinfo_path_list=[], only=None, exclude=[], filter={}):
        self.dictlists = [dictlist(id_key, path, moreinfo_path_list, only, exclude, filter) for path in path_list]

    def load_dictlist(self, id_key, path, moreinfo_path_list=[], only=None, exclude=[], filter={}):
        self.dictlists.append(dictlist(id_key, path, moreinfo_path_list, only, exclude, filter))

    def data_clean(self, only=None, exclude=[], filter={}):
        for dictlist in self.dictlists:
            dictlist.data_clean(only, exclude, filter)

    def merge(self, additional_data):
        """merge additional data into the original data"""
        for dictlist in self.dictlists:
            dictlist.merge(additional_data)

    def filter(self, filter_dict, del_en=True):
        """
        #### Function
        - filtering the data by the key and value.
        - only the data that has the key and value will remain
        - the output will always be the filtered data, but I recommend to directly use `self.data` to get the filtered data if del_en is True
        #### Input
        - filter_dict: dict; the key and value to filter the data
        - del_en: bool; if True, the data that doesn't have the key and value will be deleted from the data. If False, the data will not change but output the filtered data
        """
        for dictlist in self.dictlists:
            dictlist.filter(filter_dict, del_en)

    def del_items(self, id_list, del_by_list=True):
        """
        - id_list: list of ids
        - del_by_list: bool; if True, data having the task_id in the list will be deleted. If False, the data that doesn't have the task_id in the list will be deleted
        """
        for dictlist in self.dictlists:
            dictlist.del_items(id_list, del_by_list)

    def do(self, func:str, *args, **kwargs):
        """
        this function will perform the function `func` on all the dictlists
        for example, if you want to delete the data with task_id in the list, you can use `do("del_items", task_id_list)`
        """
        result_list = []
        for dictlist in self.dictlists:
            try:
                result_list.append(getattr(dictlist, func)(*args, **kwargs))
            except AttributeError:
                print("The function '%s' is not in dictlist"%func)
        return result_list

    def access(self, attr:str):
        """
        return the list of the attribute of the dictlist
        """
        return [getattr(dictlist, attr) for dictlist in self.dictlists]
    
    def all_equal(self, attr:str):
        """
        return True if all the attribute of the dictlist are the same
        """
        attr_list = self.access(attr)
        return all(attr == attr_list[0] for attr in attr_list)

    @property
    def num(self):
        return [dictlist.num for dictlist in self.dictlists]

    @property
    def datasets(self):
        return self.dictlists

    @property
    def groups(self):
        return self.dictlists
    

class HDLBitsProbset(dictlist):

    """ has many similarities with HDLBitsData in HDLBits_data_manager.py"""
    def __init__(self, path:str=None, more_info_paths:list=[], only_tasks:list=None, exclude_tasks:list=[], filter_content:dict={}):
        super().__init__("task_id", path=path, moreinfo_path_list=more_info_paths, only=only_tasks, exclude=exclude_tasks, filter=filter_content)

    @property
    def task_id_list(self):
        """
        return a list of task_id
        """
        return [i["task_id"] for i in self.data]
    
    def create_empty_set_via_taskids(self, task_id_list):
        """
        return a dictlist with only the task_id in the task_id_list
        """
        self.data = [{"task_id": i} for i in task_id_list]

    def access_data_via_taskid(self, task_id):
        """
        return a dict in all the information of the task_id
        """
        for i in self.data:
            if i["task_id"] == task_id:
                return i
        raise ValueError("task_id %s not found!!!" % (task_id))

if __name__ == "__main__":
    main() # run the main function