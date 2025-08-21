from solver.managers.task_manager import TASKManager
from solver.ARCKG.grid import GRID
from solver.DSL.apply_DSL import apply_DSL
from solver.DSL.transformation_DSL import coloring, make_grid

def solve():
    task_hex_code = "abbfd121"
    train_index = 0
    task_manager = TASKManager.from_hex_code(task_hex_code)
    pair = task_manager.example_pairs[train_index]
    input_grid = pair.input_grid
    tfg0 = input_grid
    tfg1 = apply_DSL(tfg0, make_grid, 7, 7, 3)
    tfg2 = apply_DSL(tfg1, coloring, [(0, 0)], 4)
    tfg3 = apply_DSL(tfg2, coloring, [(0, 1)], 5)
    tfg4 = apply_DSL(tfg3, coloring, [(0, 2)], 6)
    tfg5 = apply_DSL(tfg4, coloring, [(0, 4)], 4)
    tfg6 = apply_DSL(tfg5, coloring, [(0, 5)], 5)
    tfg7 = apply_DSL(tfg6, coloring, [(0, 6)], 6)
    tfg8 = apply_DSL(tfg7, coloring, [(1, 0)], 5)
    tfg9 = apply_DSL(tfg8, coloring, [(1, 2)], 5)
    tfg10 = apply_DSL(tfg9, coloring, [(1, 4)], 5)
    tfg11 = apply_DSL(tfg10, coloring, [(1, 6)], 5)
    tfg12 = apply_DSL(tfg11, coloring, [(2, 0)], 6)
    tfg13 = apply_DSL(tfg12, coloring, [(2, 1)], 5)
    tfg14 = apply_DSL(tfg13, coloring, [(2, 2)], 4)
    tfg15 = apply_DSL(tfg14, coloring, [(2, 4)], 6)
    tfg16 = apply_DSL(tfg15, coloring, [(2, 5)], 5)
    tfg17 = apply_DSL(tfg16, coloring, [(2, 6)], 4)
    tfg18 = apply_DSL(tfg17, coloring, [(4, 0)], 4)
    tfg19 = apply_DSL(tfg18, coloring, [(4, 1)], 5)
    tfg20 = apply_DSL(tfg19, coloring, [(4, 2)], 6)
    tfg21 = apply_DSL(tfg20, coloring, [(4, 4)], 4)
    tfg22 = apply_DSL(tfg21, coloring, [(4, 5)], 5)
    tfg23 = apply_DSL(tfg22, coloring, [(4, 6)], 6)
    tfg24 = apply_DSL(tfg23, coloring, [(5, 0)], 5)
    tfg25 = apply_DSL(tfg24, coloring, [(5, 2)], 5)
    tfg26 = apply_DSL(tfg25, coloring, [(5, 4)], 5)
    tfg27 = apply_DSL(tfg26, coloring, [(5, 6)], 5)
    tfg28 = apply_DSL(tfg27, coloring, [(6, 0)], 6)
    tfg29 = apply_DSL(tfg28, coloring, [(6, 1)], 5)
    tfg30 = apply_DSL(tfg29, coloring, [(6, 2)], 4)
    tfg31 = apply_DSL(tfg30, coloring, [(6, 4)], 6)
    tfg32 = apply_DSL(tfg31, coloring, [(6, 5)], 5)
    tfg33 = apply_DSL(tfg32, coloring, [(6, 6)], 4)
    output_grid = tfg33
    return output_grid
