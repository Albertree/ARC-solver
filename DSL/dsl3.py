from .dsl import *
from .hodel_utils import *

def get_left_top_pos(obj):
    obj = list(obj)
    leftmost_coord = 100
    topmost_coord = 100
    for i in range(len(obj)):
        if obj[i][1][0] < leftmost_coord:
            leftmost_coord = obj[i][1][0]
        if obj[i][1][1] < topmost_coord:
            topmost_coord = obj[i][1][1]
    return (leftmost_coord, topmost_coord)

def get_color(obj):
    obj = list(obj)
    # color = set()
    color = {0: False, 
             1: False, 
             2: False, 
             3: False, 
             4: False, 
             5: False, 
             6: False, 
             7: False, 
             8: False, 
             9: False 
             }

    for i in range(len(obj)):
        if color[obj[i][0]] == False:
            color[obj[i][0]] = True
        # color.add(obj[i][0])
        # color.update({obj[i][1][0]: True})
    return color

# change object list to dictionary and save the object function parameters
def find_all_objects(grid):
    grid = totuple(grid)
    object_list = []
    seen_objects = set()  # Use a set for O(1) lookups

    # Define all parameter combinations upfront
    param_combinations = [
        (True, True, True),   # single color, diagonal, background
        (False, True, True),  # single color, diagonal, no background
        (True, False, True),  # single color, not diagonal, background
        (False, False, True), # single color, not diagonal, no background
        (True, True, False),  # multiple color, diagonal, background
        (False, True, False), # multiple color, diagonal, no background
        (True, False, False), # multiple color, not diagonal, background
        (False, False, False) # multiple color, not diagonal, no background
    ]

    for univalued, diagonal, without_bg in param_combinations:
        for obj in objects(grid, univalued, diagonal, without_bg):
            # Convert object to a tuple of tuples for hashability
            obj_tuple = tuple(sorted(obj))
            if obj_tuple not in seen_objects:
                seen_objects.add(obj_tuple)
                object_info = {
                    "obj": obj,
                    "pos": get_left_top_pos(obj),
                    "color": get_color(obj),
                    "method": {"univalued": univalued, "diagonal": diagonal, "without_bg": without_bg}
                }
                object_list.append(object_info)

    return object_list


def find_all_objects_sort(grid):
    all_objects = find_all_objects(grid)

    # convert frozenset to list
    all_objects_list = []
    for obj in all_objects:
        all_objects_list.append(list(obj))

    # sort each object
    for sublist in all_objects_list:
        sublist.sort(key=lambda x: x[1])

    all_objects_list.sort(key=lambda sublist: (len(sublist), sublist[0][1]))

    return all_objects_list


def find_all_objects_sort_grid(grid):
    all_objects_list = find_all_objects_sort(grid)

    # convert colcoord to grid
    all_objects_sort_grid = []
    for obj in all_objects_list:
        grid = togrid(obj)
        all_objects_sort_grid.append(grid)

    return all_objects_sort_grid

