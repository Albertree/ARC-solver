#########################################################################
# others

# GRID
def grid_color(grid):
    return sorted(list(set([grid[i][j] for i in range(len(grid)) for j in range(len(grid[0])) if grid[i][j] != 13])))

def colorgrid_to_colcoord(colorgrid):
    return [(colorgrid[i][j], (i, j)) for i in range(len(colorgrid)) for j in range(len(colorgrid[0])) if colorgrid[i][j] != 13]


# OBJECT
def object_to_pixel_list(object):
    # return a list of tuples, each tuple is a coordinate of a pixel where the object value is not 13
    return [(i, j) for i in range(len(list(object))) for j in range(len(list(object)[0])) if list(object)[i][j] != 13]

def object_colcoord_to_colorgrid(object):
    # return a list of lists, each list has a color value of a pixel
    object = list(object)

    max_col = 0
    max_row = 0
    min_col = 100
    min_row = 100
    for n in range(len(object)):
        if object[n][1][0] > max_col:
            max_col = object[n][1][0]
        if object[n][1][1] > max_row:
            max_row = object[n][1][1] 

        if object[n][1][0] < min_col:
            min_col = object[n][1][0]
        if object[n][1][1] < min_row:
            min_row = object[n][1][1]

    if min_col == 100:
        min_col = max_col
    if min_row == 100:
        min_row = max_row
    
    if min_col == 0:
        col_move = 0
    else:
        col_move = min_col

    if min_row == 0:
        row_move = 0
    else:
        row_move = min_row

    colorgrid = [[13 for j in range(max_row - min_row + 1)] for i in range(max_col - min_col + 1)]
    for n in range(len(object)):
        colorgrid[object[n][1][0]-(col_move)][object[n][1][1]-(row_move)] = object[n][0]
    return colorgrid

# def object_to_colcoord(object):
#     # return a list of integer and integer tuple (color, (row, col))
#     return [(object[i][j], (i, j)) for i in range(len(list(object))) for j in range(len(list(object)[0])) if list(object)[i][j] != 13]

def colcoord_to_coordinate(colcoord):
    return [(colcoord[i][1][0], colcoord[i][1][1]) for i in range(len(colcoord))]

def absolute_coordinate_of_object(coordinate, pos):
    return [(coordinate[i][0] + pos[0], coordinate[i][1] + pos[1]) for i in range(len(coordinate))]

def measure_shape(object):
    # return an array of 0 or 1, 0 for value 13, 1 for other values
    shape = [[0 for j in range(len(object[0]))] for i in range(len(object))]
    for i in range(len(object)):
        for j in range(len(object[0])): 
            if object[i][j] != 13:
                shape[i][j] = 1 # 0 for valid color (color between 0 and 9)
            else:
                shape[i][j] = -1 # -1 for no color (color 13)
    return shape

def measure_area(shape):
    return sum([1 for i in range(len(shape)) for j in range(len(shape[0])) if shape[i][j] == 1])

def margin_of_grid(grid):
    margin = []
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if i == 0 or i == len(grid) - 1 or j == 0 or j == len(grid[0]) - 1:
                margin.append((i, j))
    return margin

def inner_of_grid(grid):
    inner = []  
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if i != 0 and i != len(grid) - 1 and j != 0 and j != len(grid[0]) - 1:
                inner.append((i, j))
    return inner

def corner_of_grid(grid):
    corner = []
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if (i == 0 or i == len(grid) - 1) and (j == 0 or j == len(grid[0]) - 1):
                corner.append((i, j))
    return corner

def edge_of_grid(grid):
    edge = []
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if i == 0 or i == len(grid) - 1 or j == 0 or j == len(grid[0]) - 1:
                if not ((i == 0 or i == len(grid) - 1) and (j == 0 or j == len(grid[0]) - 1)):
                    edge.append((i, j))
    return edge

def center_of_grid(grid):
    center = []
    if len(grid) % 2 == 1:
        # vertical odd, horizontal odd
        if len(grid[0]) % 2 == 1:
            center.append((len(grid) // 2, len(grid[0]) // 2))
        # vertical odd, horizontal even
        else:
            center.append((len(grid) // 2, len(grid[0]) // 2 - 1))
            center.append((len(grid) // 2, len(grid[0]) // 2))
    else:
        # vertical even, horizontal odd
        if len(grid[0]) % 2 == 1:
            center.append((len(grid) // 2 - 1, len(grid[0]) // 2))
            center.append((len(grid) // 2, len(grid[0]) // 2))
        # vertical even, horizontal even
        else:
            center.append((len(grid) // 2 - 1, len(grid[0]) // 2 - 1))
            center.append((len(grid) // 2 - 1, len(grid[0]) // 2))
            center.append((len(grid) // 2, len(grid[0]) // 2 - 1))
            center.append((len(grid) // 2, len(grid[0]) // 2))
    return center

def grid_horizontal_symmetry(grid):
    # Check if the grid is horizontally symmetric
    rows = len(grid)
    cols = len(grid[0])
    for i in range(rows // 2 + 1):
        if grid[i] != grid[rows - i - 1]:
            return False
    return True

def grid_vertical_symmetry(grid):
    # Check if the grid is vertically symmetric
    rows = len(grid)
    cols = len(grid[0])
    for j in range(cols // 2 + 1):
        for i in range(rows):
            if grid[i][j] != grid[i][cols - j - 1]:
                return False
    return True

def grid_diagonal_symmetry(grid):
    # Check if the grid is symmetric along the main diagonal
    size = len(grid)
    for i in range(size):
        for j in range(i + 1, size):
            if grid[i][j] != grid[j][i]:
                return False
    return True

def grid_antidiagonal_symmetry(grid):
    # Check if the grid is symmetric along the anti-diagonal
    size = len(grid)
    for i in range(size):
        for j in range(size - i - 1):
            if grid[i][j] != grid[size - j - 1][size - i - 1]:
                return False
    return True