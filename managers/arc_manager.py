import json
import os
from ARCKG.task import TASK, TASKInfo

class ARCManager:
    
    @staticmethod
    def from_hex_code(task_hex_code: str) -> TASK:
        possible_paths = [
            f"data/ARC_AGI/training/{task_hex_code}.json",
            f"data/ARC_AGI/evaluation/{task_hex_code}.json"
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
