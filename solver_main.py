from workers.arc_solver import ARCSolver
from managers.arc_manager import ARCManager

if __name__ == "__main__":
    # TASK_HEX_CODE = "08ed6ac7"
    TASK_HEX_CODE = "4e45f183"

    task = ARCManager.from_hex_code(TASK_HEX_CODE)

    solver = ARCSolver(task)
    # solver.temp_solve()
    # solver.test()
    solver.object_mapping()