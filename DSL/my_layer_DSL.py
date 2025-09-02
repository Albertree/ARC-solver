

def make_layer():
    return [[13 for _ in range(90)] for _ in range(90)]

def make_edit_space():
    return [[12 for _ in range(90)] for _ in range(90)]

def make_selection_layer(selection, with_color_from_main_grid=False):
    layer = make_layer()
    if with_color_from_main_grid:
        for i in range(len(selection.coordinate)):
            layer[30 + selection.coordinate[i][0]][30 + selection.coordinate[i][1]] = selection.colorgrid[selection.coordinate[i][0]][selection.coordinate[i][1]]
    else:
        for i in range(len(selection.coordinate)):
            layer[30 + selection.coordinate[i][0]][30 + selection.coordinate[i][1]] = 12 # selection color
    return layer

def make_mask(height, width):
    # print("make_mask", height, width)
    mask = [[14 for _ in range(90)] for _ in range(90)]
    # print(mask)
    for i in range(height):
        for j in range(width):
            mask[30 + i][30 + j] = 13
    return mask


def select_sub_array(matrix, row_start, row_end, col_start, col_end):
    return [row[col_start:col_end] for row in matrix[row_start:row_end]]

def paste_sub_array(mother_array, pos, sub_array):
    # Create a copy of the mother array to avoid modifying the original
    result = [row[:] for row in mother_array]
    
    row_start, col_start = pos[0], pos[1]
    row_end = min(row_start + len(sub_array), len(mother_array))
    col_end = min(col_start + len(sub_array[0]), len(mother_array[0]))
    
    for i in range(row_start, row_end):
        for j in range(col_start, col_end):
            sub_i = i - row_start
            sub_i = i - row_start
            sub_j = j - col_start
            result[i][j] = sub_array[sub_i][sub_j]
    
    return result



def merge_layers(accumulated_layers, keep_original=False):
    merged_grid = [[13 for _ in range(90)] for _ in range(90)]
    for n, layer in enumerate(accumulated_layers[:-1]):
        for i in range(len(layer)):
            for j in range(len(layer[0])):
                if layer[i][j] != 13:
                    merged_grid[i][j] = layer[i][j]
    return merged_grid 