from solver.managers.task_manager import TASKManager
from solver.ARCKG.grid import GRID
from solver.DSL.apply_DSL import apply_DSL
from solver.DSL.transformation_DSL import coloring, make_grid

def solve():
    task_hex_code = "08ed6ac7"
    train_index = 1
    task_manager = TASKManager.from_hex_code(task_hex_code)
    pair = task_manager.example_pairs[train_index]
    input_grid = pair.input_grid
    tfg0 = input_grid
    tfg1 = apply_DSL(tfg0, coloring, [(1, 7)], 1)
    tfg2 = apply_DSL(tfg1, coloring, [(2, 7)], 1)
    tfg3 = apply_DSL(tfg2, coloring, [(3, 7)], 1)
    tfg4 = apply_DSL(tfg3, coloring, [(4, 3)], 2)
    tfg5 = apply_DSL(tfg4, coloring, [(4, 7)], 1)
    tfg6 = apply_DSL(tfg5, coloring, [(5, 3)], 2)
    tfg7 = apply_DSL(tfg6, coloring, [(5, 5)], 3)
    tfg8 = apply_DSL(tfg7, coloring, [(5, 7)], 1)
    tfg9 = apply_DSL(tfg8, coloring, [(6, 3)], 2)
    tfg10 = apply_DSL(tfg9, coloring, [(6, 5)], 3)
    tfg11 = apply_DSL(tfg10, coloring, [(6, 7)], 1)
    tfg12 = apply_DSL(tfg11, coloring, [(7, 1)], 4)
    tfg13 = apply_DSL(tfg12, coloring, [(7, 3)], 2)
    tfg14 = apply_DSL(tfg13, coloring, [(7, 5)], 3)
    tfg15 = apply_DSL(tfg14, coloring, [(7, 7)], 1)
    tfg16 = apply_DSL(tfg15, coloring, [(8, 1)], 4)
    tfg17 = apply_DSL(tfg16, coloring, [(8, 3)], 2)
    tfg18 = apply_DSL(tfg17, coloring, [(8, 5)], 3)
    tfg19 = apply_DSL(tfg18, coloring, [(8, 7)], 1)
    output_grid = tfg19
    return output_grid
