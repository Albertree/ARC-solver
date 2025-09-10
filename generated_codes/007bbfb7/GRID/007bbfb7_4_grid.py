def solve(input_grid):
    added_color = []
    removed_color = []
    tfg0 = input_grid
    tfg1 = apply_DSL(tfg0, make_grid, height=9, width=9, color_to_fill=12)
    output_grid = tfg1
    return output_grid