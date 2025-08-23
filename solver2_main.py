from managers.arc_manager import ARCManager
from workers.arc_solver import ARCSolver
from comparison import *
import json
import os


if __name__ == "__main__":
    TASK_HEX_CODE = "08ed6ac7"
    
    for i in range(1000):
        TASK_HEX_CODE = ARCManager.itoj(i)
        print(i, TASK_HEX_CODE)
        task = ARCManager.from_hex_code(TASK_HEX_CODE)


