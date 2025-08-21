from solver.managers.task_manager import TASKManager
from solver.ARCKG.grid import GRID
from solver.DSL.apply_DSL import apply_DSL
from solver.DSL.transformation_DSL import coloring, make_grid

def solve():
    task_hex_code = "ac605cbb"
    train_index = 3
    task_manager = TASKManager.from_hex_code(task_hex_code)
    pair = task_manager.example_pairs[train_index]
    input_grid = pair.input_grid
    tfg0 = input_grid
    tfg1 = apply_DSL(tfg0, coloring, [(0, 3)], 6)
    tfg2 = apply_DSL(tfg1, coloring, [(1, 3)], 5)
    tfg3 = apply_DSL(tfg2, coloring, [(2, 3)], 5)
    tfg4 = apply_DSL(tfg3, coloring, [(3, 3)], 5)
    tfg5 = apply_DSL(tfg4, coloring, [(4, 1)], 2)
    tfg6 = apply_DSL(tfg5, coloring, [(4, 2)], 5)
    tfg7 = apply_DSL(tfg6, coloring, [(4, 3)], 4)
    tfg8 = apply_DSL(tfg7, coloring, [(4, 4)], 5)
    tfg9 = apply_DSL(tfg8, coloring, [(5, 2)], 4)
    tfg10 = apply_DSL(tfg9, coloring, [(5, 3)], 5)
    tfg11 = apply_DSL(tfg10, coloring, [(6, 1)], 4)
    tfg12 = apply_DSL(tfg11, coloring, [(7, 0)], 4)
    tfg13 = apply_DSL(tfg12, coloring, [(8, 9)], 1)
    tfg14 = apply_DSL(tfg13, coloring, [(9, 8)], 5)
    tfg15 = apply_DSL(tfg14, coloring, [(9, 9)], 5)
    output_grid = tfg15
    return output_grid
