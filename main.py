from managers.arc_manager import ARCManager
from managers.cli_manager import CLIManager
from workers.solver import Solver

from tools.VISUALIZATION import plot_data
import sys

def proceed(prompt="Proceed?") -> bool:
        while True:
            choice = input(prompt+" (Y/N): ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Please respond with Y or N.")


if __name__ == "__main__" :
    ### User chosen configs

    TASK_HEX_CODE = "08ed6ac7" #08ed6ac7 is color-the-histogram problem

    ###

    task = ARCManager.from_hex_code(task_hex_code=TASK_HEX_CODE)
    breakpoint()
    solver = Solver(task=task)
    solver.run()
    

    if (proceed("Solver run done. Do you want to print the run log?")) :
        solver.cli.print_log()
        exit()
    else :
        exit(1)