from solver.managers.task_manager import TASKManager
from solver.ARCKG.grid import GRID
from solver.DSL.apply_DSL import apply_DSL
from solver.DSL.transformation_DSL import coloring, make_grid

def solve():
    task_hex_code = "08ed6ac7"
    train_index = 0
    task_manager = TASKManager.from_hex_code(task_hex_code)
    pair = task_manager.example_pairs[train_index]
    input_grid = pair.input_grid
    tfg0 = input_grid
    tfg1 = apply_DSL(tfg0, coloring, [(0, 5)], 1)
    tfg2 = apply_DSL(tfg1, coloring, [(1, 1)], 2)
    tfg3 = apply_DSL(tfg2, coloring, [(1, 5)], 1)
    tfg4 = apply_DSL(tfg3, coloring, [(2, 1)], 2)
    tfg5 = apply_DSL(tfg4, coloring, [(2, 5)], 1)
    tfg6 = apply_DSL(tfg5, coloring, [(3, 1)], 2)
    tfg7 = apply_DSL(tfg6, coloring, [(3, 3)], 3)
    tfg8 = apply_DSL(tfg7, coloring, [(3, 5)], 1)
    tfg9 = apply_DSL(tfg8, coloring, [(4, 1)], 2)
    tfg10 = apply_DSL(tfg9, coloring, [(4, 3)], 3)
    tfg11 = apply_DSL(tfg10, coloring, [(4, 5)], 1)
    tfg12 = apply_DSL(tfg11, coloring, [(5, 1)], 2)
    tfg13 = apply_DSL(tfg12, coloring, [(5, 3)], 3)
    tfg14 = apply_DSL(tfg13, coloring, [(5, 5)], 1)
    tfg15 = apply_DSL(tfg14, coloring, [(6, 1)], 2)
    tfg16 = apply_DSL(tfg15, coloring, [(6, 3)], 3)
    tfg17 = apply_DSL(tfg16, coloring, [(6, 5)], 1)
    tfg18 = apply_DSL(tfg17, coloring, [(6, 7)], 4)
    tfg19 = apply_DSL(tfg18, coloring, [(7, 1)], 2)
    tfg20 = apply_DSL(tfg19, coloring, [(7, 3)], 3)
    tfg21 = apply_DSL(tfg20, coloring, [(7, 5)], 1)
    tfg22 = apply_DSL(tfg21, coloring, [(7, 7)], 4)
    tfg23 = apply_DSL(tfg22, coloring, [(8, 1)], 2)
    tfg24 = apply_DSL(tfg23, coloring, [(8, 3)], 3)
    tfg25 = apply_DSL(tfg24, coloring, [(8, 5)], 1)
    tfg26 = apply_DSL(tfg25, coloring, [(8, 7)], 4)
    output_grid = tfg26
    return output_grid
