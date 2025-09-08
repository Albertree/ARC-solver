from workers.arc_solver import ARCSolver
from managers.arc_manager import ARCManager
from basics.utils import printcg

if __name__ == "__main__":
    TASK_HEX_CODE = "08ed6ac7"
    # TASK_HEX_CODE = "007bbfb7"
    task = ARCManager.from_hex_code(TASK_HEX_CODE)

    solver = ARCSolver(task)
    # solver.try_DSL()
    solver.test() 
    