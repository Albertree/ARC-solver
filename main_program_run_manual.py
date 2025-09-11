import os

from managers.arc_manager import ARCManager
from program import ProgramManager
from basics.utils import printcg

    

if __name__ == "__main__":
    # task_hex_code = "007bbfb7"
    task_hex_code = "08ed6ac7"
    pair_index = 0
    level = ["GRID", "OBJECT", "PIXEL"]

    task = ARCManager.from_hex_code(task_hex_code)
    program_manager = ProgramManager()

    for lv in level:
        path = os.path.join(program_manager.base_output_dir, task_hex_code, lv)
        print(path)
        for file in os.listdir(path):
            if file.endswith(".py"):
                if file.split("_")[1] == str(pair_index):
                    print(file)
                    program_result = program_manager.execute_program(os.path.join(path, file), task.example_pairs[pair_index].input_grid)
                    printcg(program_result)