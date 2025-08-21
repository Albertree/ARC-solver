import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)
os.chdir(project_root)

from workers.level_1_solver import Level1Solver
from managers.task_manager import TASKManager
from tools.validate_solution import main as validate

if __name__ == "__main__":
    TASK_HEX_CODE = "08ed6ac7"
    
    task_manager = TASKManager.from_hex_code(TASK_HEX_CODE)

    for i, pair in enumerate(task_manager.example_pairs):
        solver = Level1Solver(pair.input_grid, pair.output_grid, f"{TASK_HEX_CODE}_train_{i}")
        solver.solve()

    print(f"Level 1 programs generated for task {TASK_HEX_CODE} in 'solver/result_code'")
    
    validate(TASK_HEX_CODE) 