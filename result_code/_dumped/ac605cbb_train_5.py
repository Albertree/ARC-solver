from solver.managers.task_manager import TASKManager
from solver.ARCKG.grid import GRID
from solver.DSL.apply_DSL import apply_DSL
from solver.DSL.transformation_DSL import coloring, make_grid

def solve():
    task_hex_code = "ac605cbb"
    train_index = 5
    task_manager = TASKManager.from_hex_code(task_hex_code)
    pair = task_manager.example_pairs[train_index]
    input_grid = pair.input_grid
    tfg0 = input_grid
    tfg1 = apply_DSL(tfg0, coloring, [(1, 3)], 6)
    tfg2 = apply_DSL(tfg1, coloring, [(2, 3)], 5)
    tfg3 = apply_DSL(tfg2, coloring, [(3, 3)], 5)
    tfg4 = apply_DSL(tfg3, coloring, [(4, 3)], 5)
    tfg5 = apply_DSL(tfg4, coloring, [(5, 3)], 5)
    tfg6 = apply_DSL(tfg5, coloring, [(6, 3)], 5)
    output_grid = tfg6
    return output_grid
