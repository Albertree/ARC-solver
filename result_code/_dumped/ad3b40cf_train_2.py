from solver.managers.task_manager import TASKManager
from solver.ARCKG.grid import GRID
from solver.DSL.apply_DSL import apply_DSL
from solver.DSL.transformation_DSL import coloring, make_grid

def solve():
    task_hex_code = "ad3b40cf"
    train_index = 2
    task_manager = TASKManager.from_hex_code(task_hex_code)
    pair = task_manager.example_pairs[train_index]
    input_grid = pair.input_grid
    tfg0 = input_grid
    tfg1 = apply_DSL(tfg0, coloring, [(9, 7)], 2)
    tfg2 = apply_DSL(tfg1, coloring, [(10, 6)], 2)
    tfg3 = apply_DSL(tfg2, coloring, [(10, 7)], 2)
    tfg4 = apply_DSL(tfg3, coloring, [(12, 2)], 2)
    tfg5 = apply_DSL(tfg4, coloring, [(12, 3)], 2)
    tfg6 = apply_DSL(tfg5, coloring, [(13, 2)], 2)
    tfg7 = apply_DSL(tfg6, coloring, [(13, 3)], 2)
    output_grid = tfg7
    return output_grid
