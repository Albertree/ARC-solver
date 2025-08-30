from typing import NamedTuple

from .ARCKG_component import ARCKGComponent
from .pair import PAIR, PAIRInfo

class TASKInfo(NamedTuple):
    id: int
    type: str
    raw_data: dict

class TASK(ARCKGComponent):
    def __init__(self, id: int, type: str, raw_data: dict, hex_code: str):
        super().__init__(id, type)
        self.raw_data = raw_data
        self.hex_code = hex_code

        self.example_pairs = [self.raw_data['train']]
        self.test_pairs = [self.raw_data['test']]

        self.view = self.task_dict_to_list(self.raw_data)

        self.property = dict()

    def task_dict_to_list(self, raw_data: dict) -> list:
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

        self.view_example = self.view[:self.example_pair_count]
        self.view_test = self.view[self.example_pair_count:]

        self.property['example_pair_count'] = self.example_pair_count
        self.property['test_pair_count'] = self.test_pair_count

    @staticmethod
    def from_json(task_info:TASKInfo, task_hex_code: str):
        ttt = TASK(id=task_info.id, type=task_info.type, raw_data=task_info.raw_data, hex_code=task_hex_code)
        ttt.update_property()
    
        # Create example pairs
        example_pairs = []
        for i, example in enumerate(task_info.raw_data['train']):
            example_pair_info = PAIRInfo(
                id=i,
                type='example',
                raw_data=example
            )
            pair = PAIR.from_json(example_pair_info, parent=ttt)
            example_pairs.append(pair)
        
        # Create test pairs
        test_pairs = []
        for i, test in enumerate(task_info.raw_data['test']):
            test_pair_info = PAIRInfo(
                id=i,
                type='test',
                raw_data=test
            )
            pair = PAIR.from_json(test_pair_info, parent=ttt)
            test_pairs.append(pair)

        # Set the pairs in the task
        ttt.example_pairs = example_pairs
        ttt.test_pairs = test_pairs
        
        # Update task properties
        ttt.update_property()
        ttt.to_json()
        return ttt
    
    def to_json(self):
        import os
        import json

        task_dict = self.property
        task_path = f'memory/TASK_nodes/TASK_{self.hex_code}/'
        if not os.path.exists(task_path):
            os.makedirs(task_path)

        # TASK_node - TASK_property
        path = f'{task_path}/TASK_property'
        file_name = f'TASK_{self.hex_code}_property.json'
        if not os.path.exists(path):
            os.makedirs(path)
        
        with open(f'{path}/{file_name}', 'w') as f:
            json.dump(task_dict, f, indent=2)
        
        # TASK_edge
        task_edge_path = f'memory/TASK_edges'
        if not os.path.exists(task_edge_path):
            os.makedirs(task_edge_path)
        

    def __repr__(self):
        return f"TASK(id={self.id}, type={self.type}, hex_code={self.hex_code}, example_pairs={len(self.example_pairs)}, test_pairs={len(self.test_pairs)})"