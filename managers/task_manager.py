
import json
import os
from typing import NamedTuple
from ..ARCKG.pair import PAIR, PAIRInfo

class TASKInfo(NamedTuple):
    id: int
    type: str
    raw_data: dict

class TASKManager() :
    def __init__(self, task_hex_code: str, raw_data:dict): # example_pairs:list[PAIR]=[], test_pairs:list[PAIR]=[]) -> None:
        self.task_hex_code = task_hex_code
        self.type = "task"
        self.raw_data = raw_data
    
    # turn all nested components of task dictionary to list
    def task_dict_to_list(self, raw_data:dict) -> list:
        view = []

        ttrain = []
        for i in range(len(raw_data['train'])):
            ttrain.append(list(raw_data['train'][i].values()))
        ttest = []
        for i in range(len(raw_data['test'])):
            ttest.append(list(raw_data['test'][i].values()))

        for pair in ttrain:
            view.append(pair)
        for pair in ttest:
            view.append(pair)
                   
        return view
    
    def update_property(self):
        self.example_pair_count = len(self.example_pairs) 
        self.test_pair_count = len(self.test_pairs)

        self.childs = self.example_pairs
        self.train = self.example_pairs
        self.test = self.test_pairs

        self.view = self.task_dict_to_list(self.raw_data)
        self.view_example = self.view[:self.example_pair_count]
        self.view_test = self.view[self.example_pair_count:]

    def get_example_pairs(self) -> list[PAIR]:
        return self.example_pairs

    @staticmethod
    def from_json(task_hex_code:str, raw_data:dict) :
        task_data = raw_data

        ttt = TASKManager(task_hex_code=task_hex_code, raw_data=task_data)  # Placeholder parent

        example_pairs = []
        for i, example in enumerate(raw_data['train']):
            example_pair_info = PAIRInfo(
                id = i,
                type = 'example',
                raw_data = example
            )
            ppp = PAIR.from_json(example_pair_info, parent=ttt)
            example_pairs.append(ppp)
        
        test_pairs = []
        for i, test in enumerate(raw_data['test']):
            test_pair_info = PAIRInfo(
                id = i,
                type = 'test',
                raw_data = test
            )
            ppp = PAIR.from_json(test_pair_info, parent=ttt)
            test_pairs.append(ppp)

        ttt.example_pairs = example_pairs
        ttt.test_pairs = test_pairs
        ttt.update_property()

        return ttt
    
    @staticmethod
    def from_hex_code(task_hex_code:str) :
        # Try to find the JSON file in different ARC data directories
        possible_paths = [
            f"./data/ARC_AGI/training/{task_hex_code}.json",
            f"./data/ARC_AGI/evaluation/{task_hex_code}.json"
        ]
        
        task_data = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    task_data = json.load(f)
                break
        
        if task_data is None:
            raise FileNotFoundError(f"Task file {task_hex_code}.json not found in any ARC data directory")
        
        task_manager = TASKManager.from_json(task_hex_code=task_hex_code, raw_data=task_data)

        return task_manager
    
        
    
    # @staticmethod
    # def evaluate_all(tasks:list[TASKInfo]) :
    #     # tasks 에 담긴 모든 TASK 에 대해서 채점을 앟ㅂ니다. 
    #     pass

    def __repr__(self):
        return f"TASK(task_hex_code={self.task_hex_code}, example_pairs={len(self.example_pairs)}, test_pairs={len(self.test_pairs)})"
    
    