from DSL.my_layer_DSL import make_layer

# Originate from hodel_DSL, rewritten in my style
def rot90(grid, selection):
    layer = make_layer()
    rotated_layer = [list(row) for row in zip(*selection.colorgrid[::-1])]
    for i in range(len(rotated_layer)):
        for j in range(len(rotated_layer[0])):
            layer[30 + i][30 + j] = rotated_layer[i][j]
    return layer

def rot180(grid, selection):
    layer = make_layer()
    rotated_layer = [list(row[::-1]) for row in selection.colorgrid[::-1]]
    for i in range(len(rotated_layer)):
        for j in range(len(rotated_layer[0])):
            layer[30 + i][30 + j] = rotated_layer[i][j]
    return layer

def rot270(grid, selection):
    layer = make_layer()
    rotated_layer = [list(row) for row in zip(*selection.colorgrid)][::-1]
    for i in range(len(rotated_layer)):
        for j in range(len(rotated_layer[0])):
            layer[30 + i][30 + j] = rotated_layer[i][j]
    return layer

def horizontal_flip(grid, selection):
    layer = make_layer()
    flipped_layer = selection.colorgrid[::-1]  # Reverse the order of rows
    for i in range(len(flipped_layer)):
        for j in range(len(flipped_layer[0])):
            layer[30 + i][30 + j] = flipped_layer[i][j]
    return layer
    
def vertical_flip(grid, selection):
    layer = make_layer()
    flipped_layer = [list(row[::-1]) for row in selection.colorgrid]
    for i in range(len(flipped_layer)):
        for j in range(len(flipped_layer[0])):
            layer[30 + i][30 + j] = flipped_layer[i][j]
    return layer

def diagonal_flip(grid, selection):
    layer = make_layer()
    flipped_layer = [list(row[::-1]) for row in zip(*selection.colorgrid)][::-1]
    for i in range(len(flipped_layer)):
        for j in range(len(flipped_layer[0])):
            layer[30 + i][30 + j] = flipped_layer[i][j]
    return layer

def antidiag_flip(grid, selection):
    layer = make_layer()
    flipped_layer = [list(row[::-1]) for row in zip(*selection.colorgrid[::-1])]
    for i in range(len(flipped_layer)):
        for j in range(len(flipped_layer[0])):
            layer[30 + i][30 + j] = flipped_layer[i][j]
    return layer
