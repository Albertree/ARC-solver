from solver.managers.task_manager import TASKManager
from solver.ARCKG.grid import GRID
from solver.DSL.apply_DSL import apply_DSL
from solver.DSL.transformation_DSL import coloring, make_grid

def solve():
    task_hex_code = "abbfd121"
    train_index = 2
    task_manager = TASKManager.from_hex_code(task_hex_code)
    pair = task_manager.example_pairs[train_index]
    input_grid = pair.input_grid
    tfg0 = input_grid
    tfg1 = apply_DSL(tfg0, make_grid, 6, 12, 4)
    tfg2 = apply_DSL(tfg1, coloring, [(1, 1)], 6)
    tfg3 = apply_DSL(tfg2, coloring, [(1, 2)], 5)
    tfg4 = apply_DSL(tfg3, coloring, [(1, 4)], 6)
    tfg5 = apply_DSL(tfg4, coloring, [(1, 5)], 5)
    tfg6 = apply_DSL(tfg5, coloring, [(1, 7)], 6)
    tfg7 = apply_DSL(tfg6, coloring, [(1, 8)], 5)
    tfg8 = apply_DSL(tfg7, coloring, [(1, 10)], 6)
    tfg9 = apply_DSL(tfg8, coloring, [(1, 11)], 5)
    tfg10 = apply_DSL(tfg9, coloring, [(2, 1)], 5)
    tfg11 = apply_DSL(tfg10, coloring, [(2, 2)], 6)
    tfg12 = apply_DSL(tfg11, coloring, [(2, 4)], 5)
    tfg13 = apply_DSL(tfg12, coloring, [(2, 5)], 6)
    tfg14 = apply_DSL(tfg13, coloring, [(2, 7)], 5)
    tfg15 = apply_DSL(tfg14, coloring, [(2, 8)], 6)
    tfg16 = apply_DSL(tfg15, coloring, [(2, 10)], 5)
    tfg17 = apply_DSL(tfg16, coloring, [(2, 11)], 6)
    tfg18 = apply_DSL(tfg17, coloring, [(4, 1)], 6)
    tfg19 = apply_DSL(tfg18, coloring, [(4, 2)], 5)
    tfg20 = apply_DSL(tfg19, coloring, [(4, 4)], 6)
    tfg21 = apply_DSL(tfg20, coloring, [(4, 5)], 5)
    tfg22 = apply_DSL(tfg21, coloring, [(4, 7)], 6)
    tfg23 = apply_DSL(tfg22, coloring, [(4, 8)], 5)
    tfg24 = apply_DSL(tfg23, coloring, [(4, 10)], 6)
    tfg25 = apply_DSL(tfg24, coloring, [(4, 11)], 5)
    tfg26 = apply_DSL(tfg25, coloring, [(5, 1)], 5)
    tfg27 = apply_DSL(tfg26, coloring, [(5, 2)], 6)
    tfg28 = apply_DSL(tfg27, coloring, [(5, 4)], 5)
    tfg29 = apply_DSL(tfg28, coloring, [(5, 5)], 6)
    tfg30 = apply_DSL(tfg29, coloring, [(5, 7)], 5)
    tfg31 = apply_DSL(tfg30, coloring, [(5, 8)], 6)
    tfg32 = apply_DSL(tfg31, coloring, [(5, 10)], 5)
    tfg33 = apply_DSL(tfg32, coloring, [(5, 11)], 6)
    output_grid = tfg33
    return output_grid
