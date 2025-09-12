from ARCKG.ARCKG_component import *


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

#########################################################################
# TRANSFORMATION DSL
def make_canvas(grid, selection, height, width, color_to_fill):
    layer = make_layer()
    for i in range(height):
        for j in range(width):
            layer[30 + i][30 + j] = color_to_fill
    return layer


def coloring(grid, selection, color):
    layer = make_layer()
    for coord in selection.coordinate:
        layer[30 + coord[0]][30 + coord[1]] = color
    return layer


def color_switch(grid, selection, color1, color2):
    layer = make_layer()
    for coord in selection.coordinate:
        if selection.colorgrid[coord[0]][coord[1]] == color1:
            layer[30 + coord[0]][30 + coord[1]] = color2
        elif selection.colorgrid[coord[0]][coord[1]] == color2:
            layer[30 + coord[0]][30 + coord[1]] = color1
    return layer

# hodel
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


def rotate(grid, selection, direction, iteration, pivot):
    layer = make_layer()
    
    # Normalize iteration count to 0-3 range since 4 rotations = original position
    iteration = iteration % 4
    if direction == "ccw":
        iteration = (4 - iteration) % 4

    # iteration에 따른 position 기준점
    if iteration == 0:
        position_anchor = selection.left_top
    elif iteration == 1:
        position_anchor = selection.left_bottom
    elif iteration == 2:
        position_anchor = selection.right_bottom
    elif iteration == 3:
        position_anchor = selection.right_top

    # Determine pivot point
    if type(pivot) == tuple:
        abs_rep_pivot = (pivot[0] + 30, pivot[1] + 30)
    
    if len(pivot) == 1:
        abs_rep_pivot = (pivot[0][0] + 30, pivot[0][1] + 30)
    elif len(pivot) == 4:
        # Verify the four points form a square
        rows = sorted(p[0] for p in pivot)
        cols = sorted(p[1] for p in pivot)
        if (rows[0] == rows[1] and rows[2] == rows[3] and 
            cols[0] == cols[1] and cols[2] == cols[3] and
            abs(rows[0] - rows[2]) == abs(cols[0] - cols[2])):
            abs_rep_pivot = ((rows[0] + rows[3]) // 2 + 30 + 0.5, (cols[0] + cols[3]) // 2 + 30 + 0.5) 
        else:
            raise ValueError("The four pivot points must form a square")
    else:
        raise ValueError("Pivot must be None, a single point, or four points forming a square")
        
    abs_position_anchor = (position_anchor[0] + 30, position_anchor[1] + 30)
    offset_position_anchor_from_pivot = (abs_rep_pivot[0] - abs_position_anchor[0], abs_rep_pivot[1] - abs_position_anchor[1])

    # Rotate the offset based on iteration
    if iteration == 1:  # 90 degrees
        rotated_offset_row = offset_position_anchor_from_pivot[1]
        rotated_offset_col = -offset_position_anchor_from_pivot[0]
    elif iteration == 2:  # 180 degrees
        rotated_offset_row = -offset_position_anchor_from_pivot[0]
        rotated_offset_col = -offset_position_anchor_from_pivot[1]
    elif iteration == 3:  # 270 degrees
        rotated_offset_row = -offset_position_anchor_from_pivot[1]
        rotated_offset_col = offset_position_anchor_from_pivot[0]
    else:  # 0 degrees
        rotated_offset_row = offset_position_anchor_from_pivot[0]
        rotated_offset_col = offset_position_anchor_from_pivot[1]

    rotated_position_anchor = (rotated_offset_row, rotated_offset_col)

    result_position_anchor = (int(abs_rep_pivot[0] - rotated_position_anchor[0]), int(abs_rep_pivot[1] - rotated_position_anchor[1]))

    # Get rotated object based on iteration count
    if iteration == 0:
        rotated_object = selection.bbox
    elif iteration == 1:
        rotated_object = [list(row) for row in zip(*selection.bbox[::-1])]  # rot90
    elif iteration == 2:
        rotated_object = [list(row[::-1]) for row in selection.bbox[::-1]]  # rot180
    else:  # iteration == 3
        rotated_object = [list(row) for row in zip(*selection.bbox)][::-1]  # rot270
    
    
    # Place rotated object in layer with rotated offset
    for i in range(len(rotated_object)):
        for j in range(len(rotated_object[0])):
            if 0 <= result_position_anchor[0] + i < 90 and 0 <= result_position_anchor[1] + j < 90:  # Ensure within grid bounds
                layer[result_position_anchor[0] + i][result_position_anchor[1] + j] = rotated_object[i][j]
    
    return layer

def line_flip(grid, selection, direction, pivot):
    layer = make_layer()

    if direction == "hori":
        position_anchor = selection.left_bottom
    elif direction == "verti":
        position_anchor = selection.right_top
    elif direction == "diag":
        position_anchor = selection.right_bottom
    elif direction == "anti":
        position_anchor = selection.left_top
    else:
        raise ValueError("Invalid direction")
    
    # Determine pivot point
    if type(pivot) == tuple:
        abs_rep_pivot = (pivot[0] + 30, pivot[1] + 30)
    
    if len(pivot) == 1:
        abs_rep_pivot = (pivot[0][0] + 30, pivot[0][1] + 30)
    elif len(pivot) == 4:
        # Verify the four points form a square
        rows = sorted(p[0] for p in pivot)
        cols = sorted(p[1] for p in pivot)
        if (rows[0] == rows[1] and rows[2] == rows[3] and 
            cols[0] == cols[1] and cols[2] == cols[3] and
            abs(rows[0] - rows[2]) == abs(cols[0] - cols[2])):
            abs_rep_pivot = ((rows[0] + rows[3]) // 2 + 30 + 0.5, (cols[0] + cols[3]) // 2 + 30 + 0.5) 
        else:
            raise ValueError("The four pivot points must form a square")
    else:
        raise ValueError("Pivot must be None, a single point, or four points forming a square")
        
    abs_position_anchor = (position_anchor[0] + 30, position_anchor[1] + 30)
    offset_position_anchor_from_pivot = (abs_rep_pivot[0] - abs_position_anchor[0], abs_rep_pivot[1] - abs_position_anchor[1])

    if direction == "hori":
        flipped_offset_row = -offset_position_anchor_from_pivot[0]
        flipped_offset_col = offset_position_anchor_from_pivot[1]
    elif direction == "verti":
        flipped_offset_row = offset_position_anchor_from_pivot[0]
        flipped_offset_col = -offset_position_anchor_from_pivot[1]
    elif direction == "diag":
        flipped_offset_row = -offset_position_anchor_from_pivot[1]
        flipped_offset_col = -offset_position_anchor_from_pivot[0]
    elif direction == "anti":
        flipped_offset_row = offset_position_anchor_from_pivot[1]
        flipped_offset_col = offset_position_anchor_from_pivot[0]
    else:
        raise ValueError("Invalid direction")
        
    flipped_position_anchor = (flipped_offset_row, flipped_offset_col)
    
    result_position_anchor = (int(abs_rep_pivot[0] - flipped_position_anchor[0]), int(abs_rep_pivot[1] - flipped_position_anchor[1]))
    
    # Get flipped object based on direction
    if direction == "hori":
        flipped_object = selection.bbox[::-1]
    elif direction == "verti":
        flipped_object = [list(row[::-1]) for row in selection.bbox]
    elif direction == "diag":
        flipped_object = [list(row[::-1]) for row in zip(*selection.bbox)][::-1]
    elif direction == "anti":
        flipped_object = [list(row[::-1]) for row in zip(*selection.bbox[::-1])]

    # Place flipped object in layer with flipped offset
    for i in range(len(flipped_object)):
        for j in range(len(flipped_object[0])):
            if 0 <= result_position_anchor[0] + i < 90 and 0 <= result_position_anchor[1] + j < 90:  # Ensure within grid bounds
                layer[result_position_anchor[0] + i][result_position_anchor[1] + j] = flipped_object[i][j]
    
    return layer

def point_flip(grid, selection, pivot):
    layer = make_layer()

    position_anchor = selection.right_bottom
    
    # Determine pivot point
    if type(pivot) == tuple:
        abs_rep_pivot = (pivot[0] + 30, pivot[1] + 30)
    
    if len(pivot) == 1:
        abs_rep_pivot = (pivot[0][0] + 30, pivot[0][1] + 30)
    elif len(pivot) == 4:
        # Verify the four points form a square
        rows = sorted(p[0] for p in pivot)
        cols = sorted(p[1] for p in pivot)
        if (rows[0] == rows[1] and rows[2] == rows[3] and 
            cols[0] == cols[1] and cols[2] == cols[3] and
            abs(rows[0] - rows[2]) == abs(cols[0] - cols[2])):
            abs_rep_pivot = ((rows[0] + rows[3]) // 2 + 30 + 0.5, (cols[0] + cols[3]) // 2 + 30 + 0.5) 
        else:
            raise ValueError("The four pivot points must form a square")
    else:
        raise ValueError("Pivot must be None, a single point, or four points forming a square")

    abs_position_anchor = (position_anchor[0] + 30, position_anchor[1] + 30)
    offset_position_anchor_from_pivot = (abs_rep_pivot[0] - abs_position_anchor[0], abs_rep_pivot[1] - abs_position_anchor[1])

    flipped_offset_row = -offset_position_anchor_from_pivot[0]
    flipped_offset_col = -offset_position_anchor_from_pivot[1]

    flipped_position_anchor = (flipped_offset_row, flipped_offset_col)

    result_position_anchor = (int(abs_rep_pivot[0] - flipped_position_anchor[0]), int(abs_rep_pivot[1] - flipped_position_anchor[1]))

    flipped_object = [list(row[::-1]) for row in selection.bbox[::-1]] 
    
    for i in range(len(flipped_object)):
        for j in range(len(flipped_object[0])):
            if 0 <= result_position_anchor[0] + i < 90 and 0 <= result_position_anchor[1] + j < 90:  # Ensure within grid bounds
                layer[result_position_anchor[0] + i][result_position_anchor[1] + j] = flipped_object[i][j]
    
    return layer

def move(grid, selection, direction, distance):
    layer = make_layer()
    
    position_anchor = selection.left_top
    abs_rep_position_anchor = (position_anchor[0] + 30, position_anchor[1] + 30)

    result_position_anchor = (abs_rep_position_anchor[0] + direction[0] * distance, abs_rep_position_anchor[1] + direction[1] * distance)

    for i in range(len(selection.bbox)):
        for j in range(len(selection.bbox[0])):
            if 0 <= result_position_anchor[0] + i < 90 and 0 <= result_position_anchor[1] + j < 90:  # Ensure within grid bounds
                layer[result_position_anchor[0] + i][result_position_anchor[1] + j] = selection.bbox[i][j]

    return layer

def teleport(grid, selection, grab, destination):
    layer = make_layer()

    if not grab in selection.bbox_coordinate:
        raise ValueError("Grab must be within the selection bbox.")
    
    position_anchor = selection.left_top
    # abs_rep_position_anchor = (position_anchor[0] + 30, position_anchor[1] + 30)

    offset_position_anchor_from_grab = (position_anchor[0] - grab[0], position_anchor[1] - grab[1])

    if type(destination) == list:
        destination = destination[0]
    
    abs_rep_destination = (destination[0] + 30, destination[1] + 30)

    result_position_anchor = (abs_rep_destination[0] + offset_position_anchor_from_grab[0], abs_rep_destination[1] + offset_position_anchor_from_grab[1])
    
    for i in range(len(selection.bbox)):
        for j in range(len(selection.bbox[0])):
            if 0 <= result_position_anchor[0] + i < 90 and 0 <= result_position_anchor[1] + j < 90:  # Ensure within grid bounds
                layer[result_position_anchor[0] + i][result_position_anchor[1] + j] = selection.bbox[i][j]

    return layer

def connect(grid, selection, color):
    assert len(selection.coordinate) == 2
    point1 = selection.coordinate[0]
    point2 = selection.coordinate[1]
    row_diff = point2[0] - point1[0]
    col_diff = point2[1] - point1[1]
    
    if not (point1[0] == point2[0] or point1[1] == point2[1] or abs(row_diff) == abs(col_diff)):
        raise ValueError("Coordinates must be aligned horizontally, vertically, or diagonally.")
    
    dr = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
    dc = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)
    
    steps = max(abs(row_diff), abs(col_diff))
    
    layer = make_layer()
    
    for i in range(steps + 1):
        row = point1[0] + dr * i
        col = point1[1] + dc * i
        layer[30 + row][30 + col] = color

    return layer

def straight_line(grid, selection, direction, length, color):
    # (0,1)   - right,
    # (1,1)   - down-right,
    # (1,0)   - down,
    # (1,-1)  - down-left,
    # (0,-1)  - left,
    # (-1,-1) - up-left,
    # (-1,0)  - up,
    # (-1,1)  - up-right

    assert len(selection.coordinate) == 1, "Selection must have exactly one starting coordinate."
    start = selection.coordinate[0]
    dr, dc = direction

    layer = make_layer()

    allowed = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
    if (dr, dc) not in allowed:
        raise ValueError(f"Invalid direction {direction}. Allowed directions are: {allowed}")

    for i in range(length):
        row = start[0] + dr * i
        col = start[1] + dc * i
        layer[30 + row][30 + col] = color

    return layer

def rectangle(grid, selection, color):
    assert len(selection.coordinate) == 2
    point1 = selection.coordinate[0]
    point2 = selection.coordinate[1]

    layer = make_layer()

    for i in range(point1[0], point2[0]+1):
        for j in range(point1[1], point2[1]+1):
            layer[30 + i][30 + j] = color
    return layer

def crop(grid, selection):
    layer = make_edit_space()
    for i in range(len(selection.bbox)):
        for j in range(len(selection.bbox[0])):
            layer[30 + i][30 + j] = selection.bbox[i][j]
    return layer



# def scale(selection):
#     return selection


# def paste(selection, colorgrid, handle, target):
#     # use selection and colorgrid to make a colcoord
#     colcoord = colorgrid_to_colcoord(colorgrid)
#     # use handle and target to make a list of coordinates
#     coordinates = []
#     for i in range(len(handle)):
#         for j in range(len(handle[0])):
#             if handle[i][j] == 1:
#                 coordinates.append((i, j))
#     return selection


def select_sub_array(matrix, row_start, row_end, col_start, col_end):
    return [row[col_start:col_end] for row in matrix[row_start:row_end]]

# def paste_sub_array(mother_array, pos, sub_array):
#     row_start, row_end = pos[0], pos[0]+len(sub_array)
#     col_start, col_end = pos[1], pos[1]+len(sub_array[0])
#     return [row[:col_start] + sub_array[i] + row[col_end:] for i, row in enumerate(mother_array)]

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




# 필요한 것
# copy
# paste




#########################################################################
# hodel DSL 에 있지만 아직 없는 것

# underfill -> 없어도 괜찮음
# underpaint -> 없어도 괜찮음
# 위 두 개는 배경색을 결정하거나 칠하는 기능과 연관을 지어야 한다.

# horizontal upscale
# vertical upscale
# upscale
# downscale
# 고려하고 있던 scale 기능이지만, 없어도 괜찮을 것 같다.

# horizontal concat
# vertical concat
# 그리드를 변형하고 복사해서 붙이는 기능을 하나로 합친 것인데, 하위 기능이 존재하면 없어도 괜찮지 않을까.

# subgrid
# horizontal split
# vertical split
# selection으로 커버할 수 있지 않을까.

# cellwise -> transformation 아닌 것 같다. 
# 결과가 grid가 아님. 근데 필요할지도. 대체제가 있나.

# replace -> 없어도 괜찮음
# 조건에 근거한 selection과 coloring 이면 가능하다.