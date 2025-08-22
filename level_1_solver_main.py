from workers.arc_solver import ARCSolver
from managers.arc_manager import ARCManager
from tools.validate_solution import main as validate

if __name__ == "__main__":
    TASK_HEX_CODE = "08ed6ac7"
    
    task = ARCManager.from_hex_code(TASK_HEX_CODE)

    for i, pair in enumerate(task.example_pairs):
        solver = ARCSolver(pair, f"{TASK_HEX_CODE}_train_{i}")
        solver.solve()

    print(f"Level 1 programs generated for task {TASK_HEX_CODE} in 'solver/result_code'")
    
    validate(TASK_HEX_CODE) 