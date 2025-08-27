from workers.arc_solver import ARCSolver
from managers.arc_manager import ARCManager
from tools.validate_solution import main as validate

if __name__ == "__main__":
    TASK_HEX_CODE = "08ed6ac7"

    task = ARCManager.from_hex_code(TASK_HEX_CODE)

    solver = ARCSolver(task)
    solver.temp_solve()
    # solver.temp_solve2()
    # solver.play()
    # solver.solve()

    # validate(TASK_HEX_CODE) 

