import os
import json
import glob
import random
from pathlib import Path
import shutil

class ARCDataset:
    def __init__(self):
        self.jcode_dict = self.construct_jcode_dict()

        self.preprocess_data()
        
    # load training data
    def load_data(self, dataset = "ARC_AGI", type = 'train', form = 'list_in_list', shuffle = False, jcode = True):
        if dataset == "ARC_AGI":
            path = Path('./data/ARC_AGI/')
        elif dataset == "ARC_AGI_v1":
            path = Path('./data/ARC_AGI_v1/')
        elif dataset == "ARC_AGI_v2":
            path = Path('./data/ARC_AGI_v2/')
        else:
            raise ValueError("Invalid arg 'dataset'. Please use 'ARC_AGI' or 'ARC_AGI_v1' or 'ARC_AGI_v2'.")

        if type == 'train':
            path = path / 'training'
        elif type == 'eval':
            path = path / 'evaluation'
        else:
            raise ValueError("Invalid arg 'type'. Please use 'train' or 'eval'.")


        json_files = sorted(glob.glob(os.path.join(path, '*.json')), key=lambda x: (x.lower(),x))

        tasks = []
        j_codes = []

        # nested list to tuple
        def totuple(nested_list):
            if isinstance(nested_list, list):
                return tuple(totuple(item) for item in nested_list)
            return nested_list
        
        # load json file with corresponding form (list_in_list, list_in_dict, tuple_in_list, tuple_in_dict, tuple_in_tuple)
        if form == 'list_in_list':
            for file in json_files:
                task = []
                with open(file, 'r') as f:
                    data = json.load(f)
                    task.append(data['train'])
                    ttrain = []
                    for i in range(len(data['train'])):
                        ttrain.append(list(data['train'][i].values()))
                    ttest = []
                    for i in range(len(data['test'])):
                        ttest.append(list(data['test'][i].values()))
                    task = [ttrain, ttest]                    
                tasks.append(task)
                
        elif form == 'list_in_dict':
            for file in json_files:
                with open(file, 'r') as f:
                    data = json.load(f)
                tasks.append(data)

        elif form == 'tuple_in_dict':
            # hodel
            data = {}
            for fn in os.listdir(path):
                with open(f'{path}/{fn}') as f:
                    data[fn.rstrip('.json')] = json.load(f)
            ast = lambda g: tuple(tuple(r) for r in g)
            tasks = {
                'train': {k: [{
                    'input': ast(e['input']),
                    'output': ast(e['output']),
                } for e in v['train']] for k, v in data.items()},
                'test': {k: [{
                    'input': ast(e['input']),
                    'output': ast(e['output']),
                } for e in v['test']] for k, v in data.items()}
            }

        elif form == 'tuple_in_list':
            for file in json_files:
                task = []
                with open(file, 'r') as f:
                    data = json.load(f)
                    task.append(data['train'])
                    ttrain = []
                    for i in range(len(data['train'])):
                        ttrain.append(totuple(list(data['train'][i].values())))
                    ttest = []
                    for i in range(len(data['test'])):
                        ttest.append(totuple(list(data['test'][i].values())))
                    task = [ttrain, ttest]                 
                tasks.append(task)

        elif form == 'tuple_in_tuple':
            for file in json_files:
                task = []
                with open(file, 'r') as f:
                    data = json.load(f)
                    task.append(data['train'])
                    ttrain = []
                    for i in range(len(data['train'])):
                        ttrain.append(list(data['train'][i].values()))
                    ttest = []
                    for i in range(len(data['test'])):
                        ttest.append(list(data['test'][i].values()))
                    task = [ttrain, ttest]                    
                tasks.append(task)            
            tasks = totuple(tasks)

        else:
            raise ValueError("Invalid arg 'form'. Please use 'list_in_dict' or 'list_in_list' or 'tuple_in_dict' or 'tuple_in_list' or 'tuple_in_tuple'.")
        
        # suffle tasks
        if shuffle:
            random.seed = 777
            random.shuffle(tasks)  

        # make j_codes list
        for i in range(len(json_files)):
            jcode = (json_files[i].split('.json')[0])[-8:]
            j_codes.append(jcode)
        
        if jcode:
            return tasks, j_codes
        else:
            return tasks
    
    # jcode to index
    def jtoi(self, jcode, j_codes):
        if jcode in j_codes:
            return j_codes.index(jcode)
        else: 
            return None
        
    # index to jcode
    def itoj(self, index, j_codes):
        if index < len(j_codes):
            return j_codes[index]
        else:
            return None
        
    def construct_jcode_dict(self):
        v1_train, v1_train_jcodes = self.load_data(dataset = "ARC_AGI_v1", type = 'train', form = 'list_in_list', shuffle = False, jcode = True)
        v1_eval, v1_eval_jcodes = self.load_data(dataset = "ARC_AGI_v1", type = 'eval', form = 'list_in_list', shuffle = False, jcode = True)
        v2_train, v2_train_jcodes = self.load_data(dataset = "ARC_AGI_v2", type = 'train', form = 'list_in_list', shuffle = False, jcode = True)
        v2_eval, v2_eval_jcodes = self.load_data(dataset = "ARC_AGI_v2", type = 'eval', form = 'list_in_list', shuffle = False, jcode = True)

        jcode_dict = {}

        # Initialize jcode_dict structure for v2 train jcodes
        for jcode in v2_train_jcodes:
            jcode_dict[jcode] = {
                'task_info': {
                    'v1_train': None if jcode not in v1_train_jcodes else v1_train_jcodes.index(jcode),
                    'v1_eval': None if jcode not in v1_eval_jcodes else v1_eval_jcodes.index(jcode),
                    'v2_train': None if jcode not in v2_train_jcodes else v2_train_jcodes.index(jcode),
                    'v2_eval': None if jcode not in v2_eval_jcodes else v2_eval_jcodes.index(jcode),
                }
            }
            
        # Initialize jcode_dict structure for v2 eval jcodes
        for jcode in v2_eval_jcodes:
            jcode_dict[jcode] = {
                'task_info': {
                    'v1_train': None if jcode not in v1_train_jcodes else v1_train_jcodes.index(jcode),
                    'v1_eval': None if jcode not in v1_eval_jcodes else v1_eval_jcodes.index(jcode),
                    'v2_train': None if jcode not in v2_train_jcodes else v2_train_jcodes.index(jcode),
                    'v2_eval': None if jcode not in v2_eval_jcodes else v2_eval_jcodes.index(jcode),
                }
            }
        
        # v1_train에 있는 것들 중 삭제된 것
        for jcode in v1_train_jcodes:
            if jcode not in jcode_dict.keys():
                jcode_dict[jcode] = {
                    'task_info': {
                        'v1_train': v1_train_jcodes.index(jcode),
                        'v1_eval': None,
                        'v2_train': None,
                        'v2_eval': None,
                    }
                }
        
        # v1_eval에 있는 것들 중 삭제된 것
        for jcode in v1_eval_jcodes:
            if jcode not in jcode_dict.keys():
                jcode_dict[jcode] = {
                    'task_info': {
                        'v1_train': None,
                        'v1_eval': v1_eval_jcodes.index(jcode),
                        'v2_train': None,
                        'v2_eval': None,
                    }
                }

        return jcode_dict
    
    def preprocess_data(self):
        base_folder = Path('./data/ARC_AGI')
        folders = ['training', 'evaluation']
        
        base_folder.mkdir(exist_ok=True)

        for folder in folders:
            (base_folder / folder).mkdir(exist_ok=True)

        v1_train_path = Path('./data/ARC_AGI_v1/training')
        v1_eval_path = Path('./data/ARC_AGI_v1/evaluation')
        v2_train_path = Path('./data/ARC_AGI_v2/training')
        v2_eval_path = Path('./data/ARC_AGI_v2/evaluation')

        dst_train_path = base_folder / 'training'
        dst_eval_path = base_folder / 'evaluation'

        for k, v in self.jcode_dict.items():
            if v['task_info']['v1_train'] is not None:
                if v['task_info']['v2_train'] is not None:
                    src = v1_train_path / f"{k}.json"
                    dst = dst_train_path / f"{k}.json"
                    if src.exists():
                        shutil.copy(src, dst)

            if v['task_info']['v1_eval'] is not None:
                if v['task_info']['v2_train'] is not None:
                    src = v1_eval_path / f"{k}.json"
                    dst = dst_train_path / f"{k}.json"
                    if src.exists():
                        shutil.copy(src, dst)

                if v['task_info']['v2_eval'] is not None:
                    src = v1_eval_path / f"{k}.json"
                    dst = dst_eval_path / f"{k}.json"
                    if src.exists():
                        shutil.copy(src, dst)

            if v['task_info']['v1_train'] is None and v['task_info']['v1_eval'] is None:
                if v['task_info']['v2_train'] is not None:
                    src = v2_train_path / f"{k}.json"
                    dst = dst_train_path / f"{k}.json"
                    if src.exists():
                        shutil.copy(src, dst)

                if v['task_info']['v2_eval'] is not None:
                    src = v2_eval_path / f"{k}.json"
                    dst = dst_eval_path / f"{k}.json"
                    if src.exists():
                        shutil.copy(src, dst)

