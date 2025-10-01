from managers.arc_manager import ARCManager
from workers.arc_solver import ARCSolver
from basics.utils import printcg


if __name__ == "__main__":
    # TASK_HEX_CODE = "08ed6ac7"
    # TASK_HEX_CODE = "rota000a"
    TASK_HEX_CODE = "lflp000b"

    task = ARCManager.from_hex_code(TASK_HEX_CODE)
    
    printcg(task.view)
    solver = ARCSolver(TASK_HEX_CODE)
    # solver.try_DSL()
    solver.test() 
    # solver.object_mapping()
    # for i in range(1000):
    #     TASK_HEX_CODE = ARCManager.itoj(i)
    #     print(i, TASK_HEX_CODE)
    #     task = ARCManager.from_hex_code(TASK_HEX_CODE)


