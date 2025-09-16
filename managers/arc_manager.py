import json
import os
from ARCKG.task import TASK, TASKInfo

class ARCManager:
    @staticmethod
    def _build_task_mapping():
        """
        Build mapping between task indices and their JSON hex codes.
        Returns a tuple of (index_to_json, json_to_index) dictionaries.
        """
        training_dir = "data/ARC_AGI/training"
        evaluation_dir = "data/ARC_AGI/evaluation"
        
        index_to_json = {}
        json_to_index = {}
        current_index = 0
        
        # Process training files
        if os.path.exists(training_dir):
            training_files = sorted([f for f in os.listdir(training_dir) if f.endswith('.json')])
            for filename in training_files:
                json_code = filename.replace('.json', '')
                index_to_json[current_index] = json_code
                json_to_index[json_code] = current_index
                current_index += 1
        
        # Process evaluation files
        if os.path.exists(evaluation_dir):
            evaluation_files = sorted([f for f in os.listdir(evaluation_dir) if f.endswith('.json')])
            for filename in evaluation_files:
                json_code = filename.replace('.json', '')
                index_to_json[current_index] = json_code
                json_to_index[json_code] = current_index
                current_index += 1
        
        return index_to_json, json_to_index
    
    @staticmethod
    def from_hex_code(task_hex_code: str) -> TASK:
        possible_paths = [
            f"data/ARC_AGI/training/{task_hex_code}.json",
            f"data/ARC_AGI/evaluation/{task_hex_code}.json",
            f"data/{task_hex_code}.json"
        ]
        
        task_data = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    task_data = json.load(f)
                break
        
        if task_data is None:
            raise FileNotFoundError(f"Task file {task_hex_code}.json not found in any ARC data directory")
        
        # Create and return a TASK instance with all the data
        task_info = TASKInfo(
            id=0,
            type='task',
            raw_data=task_data
        )
        ttt = TASK.from_json(task_info, task_hex_code)
        
        return ttt
    
    @staticmethod
    def itoj(i: int) -> str:
        index_to_json, _ = ARCManager._build_task_mapping()
        if i not in index_to_json:
            raise ValueError(f"Task index {i} not found in mapping")
        return index_to_json[i]
    
    @staticmethod
    def jtoi(json_code: str) -> int:
        _, json_to_index = ARCManager._build_task_mapping()
        if json_code not in json_to_index:
            raise ValueError(f"JSON code {json_code} not found in mapping")
        return json_to_index[json_code]
