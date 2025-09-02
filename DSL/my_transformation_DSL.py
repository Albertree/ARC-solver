from DSL.my_layer_DSL import make_layer, make_edit_space
from DSL.hodel_arc_types import *


# basic transformation DSLs
# 0. make_grid
def make_grid(grid, height=int, width=int, color_to_fill=int):
    layer = make_layer()
    for i in range(height):
        for j in range(width):
            layer[30 + i][30 + j] = color_to_fill
    return layer

# 1. coloring
def coloring(grid, selection, color):
    layer = make_layer()
    for coord in selection.coordinate:
        layer[30 + coord[0]][30 + coord[1]] = color
    return layer

# 2. color_switch
def color_switch(grid, selection, color1, color2):
    layer = make_layer()
    for coord in selection.coordinate:
        if selection.colorgrid[coord[0]][coord[1]] == color1:
            layer[30 + coord[0]][30 + coord[1]] = color2
        elif selection.colorgrid[coord[0]][coord[1]] == color2:
            layer[30 + coord[0]][30 + coord[1]] = color1
    return layer

# 3. rotate
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
    
    # pprint("rotated_object", rotated_object)
    
    # Place rotated object in layer with rotated offset
    for i in range(len(rotated_object)):
        for j in range(len(rotated_object[0])):
            if 0 <= result_position_anchor[0] + i < 90 and 0 <= result_position_anchor[1] + j < 90:  # Ensure within grid bounds
                layer[result_position_anchor[0] + i][result_position_anchor[1] + j] = rotated_object[i][j]
    
    return layer

# 4. line_flip
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

# 5. move
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

# 6. teleport
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

# 7. connect
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

# 8. straight_line
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

# 9. rectangle
def rectangle(grid, selection, color):
    assert len(selection.coordinate) == 2
    point1 = selection.coordinate[0]
    point2 = selection.coordinate[1]

    layer = make_layer()

    for i in range(point1[0], point2[0]+1):
        for j in range(point1[1], point2[1]+1):
            layer[30 + i][30 + j] = color
    return layer

# 10. crop
def crop(grid, selection):
    layer = make_edit_space()
    for i in range(len(selection.bbox)):
        for j in range(len(selection.bbox[0])):
            layer[30 + i][30 + j] = selection.bbox[i][j]
    return layer



# 필요한 것
# copy
# paste
# scale


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









#########################################################################
# TRANSFORMATION DSL

# CAUTION!! TF DSL 중 make_canvas 함수에 변경사항이 있습니다.
# 다른 TF DSL 함수에는 selection 이라는 인자가 반드시 필요해서 통일성을 위해 make_canvas 함수에도 포함을 시켰지만,
# 필요하지 않고, 함수의 직관성을 저해한다고 판단되어 make_canvas 함수에서 selection 인자를 제거했습니다.
# 그리고 함수의 이름에 canvas라는 ARC 도메인에서 사용되지 않는 단어가 있어서 부르고 기억하기 어렵다고 판단되었습니다.
# 이에 make_canvas 함수를 make_grid 함수로 이름을 변경했습니다.
# 2025 0708 - 이석기

# def make_canvas(grid, selection, height, width, color_to_fill):
#     layer = make_layer()
#     for i in range(height):
#         for j in range(width):
#             layer[30 + i][30 + j] = color_to_fill
#     return layer






