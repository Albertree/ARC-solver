from managers.arc_manager import ARCManager
from workers.arc_solver import ARCSolver

if __name__ == "__main__":
    TASK_HEX_CODE = "08ed6ac7"
    TASK_HEX_CODE = "6a1e5592"

    # TASK_HEX_CODE = ARCManager.itoj(909)

    task = ARCManager.from_hex_code(TASK_HEX_CODE)
    
    solver = ARCSolver(task)
    solver.object_mapping()
    # for i in range(1000):
    #     TASK_HEX_CODE = ARCManager.itoj(i)
    #     print(i, TASK_HEX_CODE)
    #     task = ARCManager.from_hex_code(TASK_HEX_CODE)


