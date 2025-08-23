from basics.ARCLOADER import *
from basics.VISUALIZATION import *
from ARCKG_components import *

import pickle
import copy
import json
import numpy as np

grid_compare_category_list = ["size", "color", "area", "symmetry"]
object_compare_category_list = ["method", "size", "position", "color", "area", "shape", "symmetry"]
pixel_compare_category_list = ["color", "coordinate"]

compare_result_template = {
    "comp1_id": None,
    "comp2_id": None,
    "category": {}
}

expression_unit_template = {
    "type": None,
    "comp1": None,
    "comp2": None,
    "delta": None
}

def horizontal_flip(matrix):
    """Flip matrix horizontally (left-right)"""
    return np.fliplr(matrix)

def vertical_flip(matrix):
    """Flip matrix vertically (up-down)"""
    return np.flipud(matrix)

def diagonal_flip(matrix):
    """Flip matrix along main diagonal (transpose)"""
    return np.transpose(matrix)

def anti_diagonal_flip(matrix):
    """Flip matrix along anti-diagonal"""
    return np.transpose(np.flipud(np.fliplr(matrix)))

def rotate90(matrix):
    """Rotate matrix 90 degrees clockwise"""
    return np.rot90(matrix, k=-1)

def rotate180(matrix):
    """Rotate matrix 180 degrees"""
    return np.rot90(matrix, k=2)

def rotate270(matrix):
    """Rotate matrix 270 degrees clockwise (90 degrees counter-clockwise)"""
    return np.rot90(matrix, k=1)

def check_alternatives(comp1_matrix, comp2_matrix):
    """Check if comp1_matrix matches any transformation of comp2_matrix"""
    transformations = [
        horizontal_flip,
        vertical_flip,
        diagonal_flip,
        anti_diagonal_flip,
        rotate90,
        rotate180,
        rotate270
    ]
    
    # Check if matrices are the same without transformation
    if np.array_equal(comp1_matrix, comp2_matrix):
        return True
    
    # Check each transformation
    for transform_func in transformations:
        try:
            transformed = transform_func(comp2_matrix)
            if np.array_equal(comp1_matrix, transformed):
                return True
        except:
            continue
    
    return False

def grid_compare(comp1, comp2):
    # print(f"Comparing grids: {comp1.id} and {comp2.id}")

    # initialize the result template
    grid_compare_result = copy.deepcopy(compare_result_template)
    grid_compare_result["comp1_id"] = str(comp1.id)
    grid_compare_result["comp2_id"] = str(comp2.id)
    grid_compare_result["category"] = {key: {} for key in grid_compare_category_list}

    # Define all property lists first
    size_props = ["height", "width"]
    
    color1 = set(comp1.color)
    color2 = set(comp2.color)
    union_colorset = color1.union(color2)
    color_props = [color for color in union_colorset]
    color_props.append("num_of_colors")
    
    area_props = [color for color in union_colorset]
    area_props.append("total")
    
    symmetry_props = ["hori_symm", "verti_symm", "diag_symm", "anti_symm"]

    # initialize the categories and properties based on component information
    for key in grid_compare_result["category"]:
        if key == "size":
            for e in size_props:
                grid_compare_result["category"]["size"][e] = copy.deepcopy(expression_unit_template)
            
        if key == "color":
            for e in color_props:
                grid_compare_result["category"]["color"][e] = copy.deepcopy(expression_unit_template)

        if key == "area":
            for e in area_props:
                grid_compare_result["category"]["area"][e] = copy.deepcopy(expression_unit_template)

        if key == "symmetry":
            for e in symmetry_props:
                grid_compare_result["category"]["symmetry"][e] = copy.deepcopy(expression_unit_template)

    # compare the properties
    for key in grid_compare_result["category"]:
        if key == "size":
            for prop in size_props:
                comp1_value = getattr(comp1, prop)
                comp2_value = getattr(comp2, prop)
                
                if comp1_value == comp2_value:
                    grid_compare_result["category"]["size"][prop]["type"] = "COMM"
                    grid_compare_result["category"]["size"][prop]["comp1"] = comp1_value
                    grid_compare_result["category"]["size"][prop]["comp2"] = comp2_value
                    grid_compare_result["category"]["size"][prop]["delta"] = "0"
                else:
                    grid_compare_result["category"]["size"][prop]["type"] = "DIFF"
                    grid_compare_result["category"]["size"][prop]["comp1"] = comp1_value
                    grid_compare_result["category"]["size"][prop]["comp2"] = comp2_value
                    grid_compare_result["category"]["size"][prop]["delta"] = f"{comp2_value - comp1_value:+}"
            
        if key == "color":
            for prop in color_props:
                if prop == "num_of_colors":
                    comp1_value = len(comp1.color)
                    comp2_value = len(comp2.color)

                    if comp1_value == comp2_value:
                        grid_compare_result["category"]["color"][prop]["type"] = "COMM"
                        grid_compare_result["category"]["color"][prop]["comp1"] = comp1_value
                        grid_compare_result["category"]["color"][prop]["comp2"] = comp2_value
                        grid_compare_result["category"]["color"][prop]["delta"] = "0"
                    else:
                        grid_compare_result["category"]["color"][prop]["type"] = "DIFF"
                        grid_compare_result["category"]["color"][prop]["comp1"] = comp1_value
                        grid_compare_result["category"]["color"][prop]["comp2"] = comp2_value
                        grid_compare_result["category"]["color"][prop]["delta"] = f"{comp2_value - comp1_value:+}"

                else: # prop is a color (int)
                    comp1_value = comp1.color
                    comp2_value = comp2.color
                    # color in both comp1 and comp2
                    if prop in comp1_value and prop in comp2_value:
                        grid_compare_result["category"]["color"][prop]["type"] = "COMM"
                        grid_compare_result["category"]["color"][prop]["comp1"] = True
                        grid_compare_result["category"]["color"][prop]["comp2"] = True
                        grid_compare_result["category"]["color"][prop]["delta"] = "="
                    # color in comp1 but not in comp2
                    elif prop in comp1_value and prop not in comp2_value:
                        grid_compare_result["category"]["color"][prop]["type"] = "DIFF"
                        grid_compare_result["category"]["color"][prop]["comp1"] = True
                        grid_compare_result["category"]["color"][prop]["comp2"] = False
                        grid_compare_result["category"]["color"][prop]["delta"] = "-"
                    # color in comp2 but not in comp1
                    elif prop not in comp1_value and prop in comp2_value:
                        grid_compare_result["category"]["color"][prop]["type"] = "DIFF"
                        grid_compare_result["category"]["color"][prop]["comp1"] = False
                        grid_compare_result["category"]["color"][prop]["comp2"] = True
                        grid_compare_result["category"]["color"][prop]["delta"] = "+"
        
        if key == "area":
            for prop in area_props:
                if prop == "total":
                    comp1_value = comp1.area
                    comp2_value = comp2.area

                    if comp1_value == comp2_value:
                        grid_compare_result["category"]["area"][prop]["type"] = "COMM"
                        grid_compare_result["category"]["area"][prop]["comp1"] = comp1_value
                        grid_compare_result["category"]["area"][prop]["comp2"] = comp2_value
                        grid_compare_result["category"]["area"][prop]["delta"] = "0"
                    else:
                        grid_compare_result["category"]["area"][prop]["type"] = "DIFF"
                        grid_compare_result["category"]["area"][prop]["comp1"] = comp1_value
                        grid_compare_result["category"]["area"][prop]["comp2"] = comp2_value
                        grid_compare_result["category"]["area"][prop]["delta"] = f"{comp2_value - comp1_value:+}"

                else: # prop is a color (int)
                    comp1_value = 0
                    for x in comp1.pixels:
                        if x.color == prop:
                            comp1_value += 1

                    comp2_value = 0
                    for x in comp2.pixels:
                        if x.color == prop:
                            comp2_value += 1

                    if comp1_value == comp2_value:
                        grid_compare_result["category"]["area"][prop]["type"] = "COMM"
                        grid_compare_result["category"]["area"][prop]["comp1"] = comp1_value
                        grid_compare_result["category"]["area"][prop]["comp2"] = comp2_value
                        grid_compare_result["category"]["area"][prop]["delta"] = "0"
                    else:
                        grid_compare_result["category"]["area"][prop]["type"] = "DIFF"
                        grid_compare_result["category"]["area"][prop]["comp1"] = comp1_value
                        grid_compare_result["category"]["area"][prop]["comp2"] = comp2_value
                        grid_compare_result["category"]["area"][prop]["delta"] = f"{comp2_value - comp1_value:+}"
        
        if key == "symmetry":
            for prop in symmetry_props:
                comp1_value = getattr(comp1, prop)
                comp2_value = getattr(comp2, prop)

                if comp1_value == comp2_value:
                    grid_compare_result["category"]["symmetry"][prop]["type"] = "COMM"
                    grid_compare_result["category"]["symmetry"][prop]["comp1"] = comp1_value
                    grid_compare_result["category"]["symmetry"][prop]["comp2"] = comp2_value
                    grid_compare_result["category"]["symmetry"][prop]["delta"] = "="
                else:
                    grid_compare_result["category"]["symmetry"][prop]["type"] = "DIFF"
                    grid_compare_result["category"]["symmetry"][prop]["comp1"] = comp1_value
                    grid_compare_result["category"]["symmetry"][prop]["comp2"] = comp2_value
                    grid_compare_result["category"]["symmetry"][prop]["delta"] = "x"
    
    return grid_compare_result

def object_compare(comp1, comp2):
    # print(f"Comparing objects: {comp1.id} and {comp2.id}")

    # initialize the result template
    object_compare_result = copy.deepcopy(compare_result_template)
    object_compare_result["comp1_id"] = str(comp1.id)
    object_compare_result["comp2_id"] = str(comp2.id)
    object_compare_result["category"] = {key: {} for key in object_compare_category_list}

    # Define all property lists first
    # no method_props 
    size_props = ["height", "width"]
    position_props = ["left_top", "right_top", "left_bottom", "right_bottom"]
    sub_position_props = ["row_pos", "col_pos"]
    
    color1 = set(comp1.color) if hasattr(comp1, 'color') else set()
    color2 = set(comp2.color) if hasattr(comp2, 'color') else set()
    union_colorset = color1.union(color2)
    color_props = [color for color in union_colorset]
    color_props.append("num_of_colors")
    
    area_props = [color for color in union_colorset]
    area_props.append("total")
    
    # no shape_props
    symmetry_props = ["hori_symm", "verti_symm", "diag_symm", "anti_symm"]

    # initialize the categories and properties based on component information
    for key in object_compare_result["category"]:
        if key == "method":
            object_compare_result["category"]["method"] = copy.deepcopy(expression_unit_template)
        
        if key == "size":
            for e in size_props:
                object_compare_result["category"]["size"][e] = copy.deepcopy(expression_unit_template)
            
        if key == "position":
            for e in position_props:
                object_compare_result["category"]["position"][e] = {}
                for sub_e in sub_position_props:
                    object_compare_result["category"]["position"][e][sub_e] = copy.deepcopy(expression_unit_template)
        
        if key == "color":
            for e in color_props:
                object_compare_result["category"]["color"][e] = copy.deepcopy(expression_unit_template)

        if key == "area":
            for e in area_props:
                object_compare_result["category"]["area"][e] = copy.deepcopy(expression_unit_template)
                
        if key == "shape":
            object_compare_result["category"]["shape"] = copy.deepcopy(expression_unit_template)

        if key == "symmetry":
            for e in symmetry_props:
                object_compare_result["category"]["symmetry"][e] = copy.deepcopy(expression_unit_template)

    # compare the properties
    for key in object_compare_result["category"]:
        if key == "method":
            comp1_value = getattr(comp1, "method", None)
            comp2_value = getattr(comp2, "method", None)
                
            if comp1_value == comp2_value:
                object_compare_result["category"]["method"]["type"] = "COMM"
                object_compare_result["category"]["method"]["comp1"] = comp1_value
                object_compare_result["category"]["method"]["comp2"] = comp2_value
                object_compare_result["category"]["method"]["delta"] = "="
            else:
                object_compare_result["category"]["method"]["type"] = "DIFF"
                object_compare_result["category"]["method"]["comp1"] = comp1_value
                object_compare_result["category"]["method"]["comp2"] = comp2_value
                object_compare_result["category"]["method"]["delta"] = "x"
        
        if key == "size":
            for prop in size_props:
                comp1_value = getattr(comp1, prop, 0)
                comp2_value = getattr(comp2, prop, 0)
                
                if comp1_value == comp2_value:
                    object_compare_result["category"]["size"][prop]["type"] = "COMM"
                    object_compare_result["category"]["size"][prop]["comp1"] = comp1_value
                    object_compare_result["category"]["size"][prop]["comp2"] = comp2_value
                    object_compare_result["category"]["size"][prop]["delta"] = "0"
                else:
                    object_compare_result["category"]["size"][prop]["type"] = "DIFF"
                    object_compare_result["category"]["size"][prop]["comp1"] = comp1_value
                    object_compare_result["category"]["size"][prop]["comp2"] = comp2_value
                    object_compare_result["category"]["size"][prop]["delta"] = f"{comp2_value - comp1_value:+}"
                    
        if key == "position":
            for prop in position_props:
                if prop == "left_top":
                    comp1_pos = getattr(comp1, "left_top")
                    comp2_pos = getattr(comp2, "left_top")
                elif prop == "right_top":
                    comp1_pos = getattr(comp1, "right_top")
                    comp2_pos = getattr(comp2, "right_top")
                elif prop == "left_bottom":
                    comp1_pos = getattr(comp1, "left_bottom")
                    comp2_pos = getattr(comp2, "left_bottom")
                elif prop == "right_bottom":
                    comp1_pos = getattr(comp1, "right_bottom")
                    comp2_pos = getattr(comp2, "right_bottom")

                for sub_prop in sub_position_props:
                    if sub_prop == "row_pos":
                        comp1_value = comp1_pos[0]
                        comp2_value = comp2_pos[0]
                    elif sub_prop == "col_pos":
                        comp1_value = comp1_pos[1]
                        comp2_value = comp2_pos[1]

                    if comp1_value == comp2_value:
                        object_compare_result["category"]["position"][prop][sub_prop]["type"] = "COMM"
                        object_compare_result["category"]["position"][prop][sub_prop]["comp1"] = comp1_value
                        object_compare_result["category"]["position"][prop][sub_prop]["comp2"] = comp2_value
                        object_compare_result["category"]["position"][prop][sub_prop]["delta"] = "0"
                    else:
                        object_compare_result["category"]["position"][prop][sub_prop]["type"] = "DIFF"
                        object_compare_result["category"]["position"][prop][sub_prop]["comp1"] = comp1_value
                        object_compare_result["category"]["position"][prop][sub_prop]["comp2"] = comp2_value
                        object_compare_result["category"]["position"][prop][sub_prop]["delta"] = f"{comp2_value - comp1_value:+}"

        if key == "color":
            for prop in color_props:
                if prop == "num_of_colors":
                    comp1_value = len(comp1.color)
                    comp2_value = len(comp2.color)

                    if comp1_value == comp2_value:
                        object_compare_result["category"]["color"][prop]["type"] = "COMM"
                        object_compare_result["category"]["color"][prop]["comp1"] = comp1_value
                        object_compare_result["category"]["color"][prop]["comp2"] = comp2_value
                        object_compare_result["category"]["color"][prop]["delta"] = "0"
                    else:
                        object_compare_result["category"]["color"][prop]["type"] = "DIFF"
                        object_compare_result["category"]["color"][prop]["comp1"] = comp1_value
                        object_compare_result["category"]["color"][prop]["comp2"] = comp2_value
                        object_compare_result["category"]["color"][prop]["delta"] = f"{comp2_value - comp1_value:+}"

                else: # prop is a color (int)
                    comp1_value = comp1.color
                    comp2_value = comp2.color
                    # color in both comp1 and comp2
                    if prop in comp1_value and prop in comp2_value:
                        object_compare_result["category"]["color"][prop]["type"] = "COMM"
                        object_compare_result["category"]["color"][prop]["comp1"] = True
                        object_compare_result["category"]["color"][prop]["comp2"] = True
                        object_compare_result["category"]["color"][prop]["delta"] = "="
                    # color in comp1 but not in comp2
                    elif prop in comp1_value and prop not in comp2_value:
                        object_compare_result["category"]["color"][prop]["type"] = "DIFF"
                        object_compare_result["category"]["color"][prop]["comp1"] = True
                        object_compare_result["category"]["color"][prop]["comp2"] = False
                        object_compare_result["category"]["color"][prop]["delta"] = "-"
                    # color in comp2 but not in comp1
                    elif prop not in comp1_value and prop in comp2_value:
                        object_compare_result["category"]["color"][prop]["type"] = "DIFF"
                        object_compare_result["category"]["color"][prop]["comp1"] = False
                        object_compare_result["category"]["color"][prop]["comp2"] = True
                        object_compare_result["category"]["color"][prop]["delta"] = "+"
        
        if key == "area":
            for prop in area_props:
                if prop == "total":
                    comp1_value = getattr(comp1, 'area')
                    comp2_value = getattr(comp2, 'area')

                    if comp1_value == comp2_value:
                        object_compare_result["category"]["area"][prop]["type"] = "COMM"
                        object_compare_result["category"]["area"][prop]["comp1"] = comp1_value
                        object_compare_result["category"]["area"][prop]["comp2"] = comp2_value
                        object_compare_result["category"]["area"][prop]["delta"] = "0"
                    else:
                        object_compare_result["category"]["area"][prop]["type"] = "DIFF"
                        object_compare_result["category"]["area"][prop]["comp1"] = comp1_value
                        object_compare_result["category"]["area"][prop]["comp2"] = comp2_value
                        object_compare_result["category"]["area"][prop]["delta"] = f"{comp2_value - comp1_value:+}"

                else: # prop is a color (int)
                    comp1_value = 0
                    if hasattr(comp1, 'childs'):
                        for x in comp1.childs:
                            if x.color == prop:
                                comp1_value += 1

                    comp2_value = 0
                    if hasattr(comp2, 'childs'):
                        for x in comp2.childs:
                            if x.color == prop:
                                comp2_value += 1

                    if comp1_value == comp2_value:
                        object_compare_result["category"]["area"][prop]["type"] = "COMM"
                        object_compare_result["category"]["area"][prop]["comp1"] = comp1_value
                        object_compare_result["category"]["area"][prop]["comp2"] = comp2_value
                        object_compare_result["category"]["area"][prop]["delta"] = "0"
                    else:
                        object_compare_result["category"]["area"][prop]["type"] = "DIFF"
                        object_compare_result["category"]["area"][prop]["comp1"] = comp1_value
                        object_compare_result["category"]["area"][prop]["comp2"] = comp2_value
                        object_compare_result["category"]["area"][prop]["delta"] = f"{comp2_value - comp1_value:+}"
                        
        if key == "shape":
            comp1_value = getattr(comp1, "shape")
            comp2_value = getattr(comp2, "shape")
                
            # Try transformation checking first if both values exist
            shapes_match = False
            if comp1_value is not None and comp2_value is not None:
                try:
                    comp1_matrix = np.array(comp1_value)
                    comp2_matrix = np.array(comp2_value)
                    shapes_match = check_alternatives(comp1_matrix, comp2_matrix)
                except:
                    # Fall back to simple comparison if matrix operations fail
                    shapes_match = (comp1_value == comp2_value)
            else:
                # Simple comparison for None or invalid values
                shapes_match = (comp1_value == comp2_value)
            
            if shapes_match:
                object_compare_result["category"]["shape"]["type"] = "COMM"
                object_compare_result["category"]["shape"]["comp1"] = comp1_value
                object_compare_result["category"]["shape"]["comp2"] = comp2_value
                object_compare_result["category"]["shape"]["delta"] = "="
            else:
                object_compare_result["category"]["shape"]["type"] = "DIFF"
                object_compare_result["category"]["shape"]["comp1"] = comp1_value
                object_compare_result["category"]["shape"]["comp2"] = comp2_value
                object_compare_result["category"]["shape"]["delta"] = "x"
    
        if key == "symmetry":
            for prop in symmetry_props:
                comp1_value = getattr(comp1, prop)
                comp2_value = getattr(comp2, prop)

                if comp1_value == comp2_value:
                    object_compare_result["category"]["symmetry"][prop]["type"] = "COMM"
                    object_compare_result["category"]["symmetry"][prop]["comp1"] = comp1_value
                    object_compare_result["category"]["symmetry"][prop]["comp2"] = comp2_value
                    object_compare_result["category"]["symmetry"][prop]["delta"] = "="
                else:
                    object_compare_result["category"]["symmetry"][prop]["type"] = "DIFF"
                    object_compare_result["category"]["symmetry"][prop]["comp1"] = comp1_value
                    object_compare_result["category"]["symmetry"][prop]["comp2"] = comp2_value
                    object_compare_result["category"]["symmetry"][prop]["delta"] = "x"
    
    return object_compare_result

def pixel_compare(comp1, comp2):
    # print(f"Comparing pixels: {comp1.id} and {comp2.id}")

    # initialize the result template
    pixel_compare_result = copy.deepcopy(compare_result_template)
    pixel_compare_result["comp1_id"] = str(comp1.id)
    pixel_compare_result["comp2_id"] = str(comp2.id)
    pixel_compare_result["category"] = {key: {} for key in pixel_compare_category_list}

    # Define all property lists first
    color_props = ["color"]
    coordinate_props = ["row", "col"]  # assuming pixels have row, col coordinates

    # initialize the categories and properties based on component information
    for key in pixel_compare_result["category"]:
        if key == "color":
            for e in color_props:
                pixel_compare_result["category"]["color"][e] = copy.deepcopy(expression_unit_template)
            
        if key == "coordinate":
            for e in coordinate_props:
                pixel_compare_result["category"]["coordinate"][e] = copy.deepcopy(expression_unit_template)

    # compare the properties
    for key in pixel_compare_result["category"]:
        if key == "color":
            for prop in color_props:
                comp1_value = getattr(comp1, prop, None)
                comp2_value = getattr(comp2, prop, None)
                
                if comp1_value == comp2_value:
                    pixel_compare_result["category"]["color"][prop]["type"] = "COMM"
                    pixel_compare_result["category"]["color"][prop]["comp1"] = comp1_value
                    pixel_compare_result["category"]["color"][prop]["comp2"] = comp2_value
                    pixel_compare_result["category"]["color"][prop]["delta"] = "="
                else:
                    pixel_compare_result["category"]["color"][prop]["type"] = "DIFF"
                    pixel_compare_result["category"]["color"][prop]["comp1"] = comp1_value
                    pixel_compare_result["category"]["color"][prop]["comp2"] = comp2_value
                    pixel_compare_result["category"]["color"][prop]["delta"] = "x"
        
        if key == "coordinate":
            for prop in coordinate_props:
                # Handle coordinate access - assuming pixels have pos attribute with [row, col]
                comp1_pos = getattr(comp1, "coordinate")
                comp2_pos = getattr(comp2, "coordinate")
                
                if prop == "row":
                    comp1_value = comp1_pos[0]
                    comp2_value = comp2_pos[0]
                elif prop == "col":
                    comp1_value = comp1_pos[1]
                    comp2_value = comp2_pos[1]
                
                if comp1_value == comp2_value:
                    pixel_compare_result["category"]["coordinate"][prop]["type"] = "COMM"
                    pixel_compare_result["category"]["coordinate"][prop]["comp1"] = comp1_value
                    pixel_compare_result["category"]["coordinate"][prop]["comp2"] = comp2_value
                    pixel_compare_result["category"]["coordinate"][prop]["delta"] = "0"
                else:
                    pixel_compare_result["category"]["coordinate"][prop]["type"] = "DIFF"
                    pixel_compare_result["category"]["coordinate"][prop]["comp1"] = comp1_value
                    pixel_compare_result["category"]["coordinate"][prop]["comp2"] = comp2_value
                    pixel_compare_result["category"]["coordinate"][prop]["delta"] = f"{comp2_value - comp1_value:+}"
    
    return pixel_compare_result

def compare(comp1, comp2):
    if comp1.type == "grid" and comp2.type == "grid":
        return grid_compare(comp1, comp2)
    elif comp1.type == "object" and comp2.type == "object":
        return object_compare(comp1, comp2)
    elif comp1.type == "pixel" and comp2.type == "pixel":
        return pixel_compare(comp1, comp2)
    else:
        raise ValueError("Invalid comparison type. Check the component id.")
    

if __name__ == "__main__":
    with open("everything_train.pkl", "rb") as f:
        everything = pickle.load(f)
    
    #########################################################
    # grid compare example
    #########################################################

    tnum = 123
    pnum = 0

    id1 = (tnum, pnum, 0, None, None)
    id2 = (tnum, pnum, 1, None, None)

    comp1 = next(comp for comp in everything if comp.id == id1)
    comp2 = next(comp for comp in everything if comp.id == id2)

    grid_result = compare(comp1, comp2)

    with open("example_grid_comparison_receipt.json", "w") as f:
        json.dump(grid_result, f, indent=2)
    

    
    # visualize the comparing grids
    comparing_grids = []
    g1 = next(comp for comp in everything if comp.id == id1)
    g2 = next(comp for comp in everything if comp.id == id2)
    comparing_grids.append(g1.view)
    comparing_grids.append(g2.view)

    plot_data(comparing_grids)




    #########################################################
    # object compare example
    #########################################################

    tnum = 280
    pnum = 0
    gnum = 1
    onum1 = 2
    onum2 = 0

    id3 = (tnum, pnum, gnum, onum1, None)
    id4 = (tnum, pnum, gnum, onum2, None)

    comp3 = next(comp for comp in everything if comp.id == id3)
    comp4 = next(comp for comp in everything if comp.id == id4)

    object_result = compare(comp3, comp4)
    
    with open("example_object_comparison_receipt.json", "w") as f:
        json.dump(object_result, f, indent=2)



    # visualize the comparing objects
    comparing_objects = []
    o1 = next(comp for comp in everything if comp.id == id3)
    o2 = next(comp for comp in everything if comp.id == id4)
    comparing_objects.append(o1.view)
    comparing_objects.append(o2.view)

    plot_data(comparing_objects)





    #########################################################
    # pixel compare example
    #########################################################

    tnum = 280
    pnum = 0
    gnum = 1
    onum = None
    xnum1 = 0
    xnum2 = 3

    id5 = (tnum, pnum, gnum, onum, xnum1)
    id6 = (tnum, pnum, gnum, onum, xnum2)

    comp5 = next(comp for comp in everything if comp.id == id5)
    comp6 = next(comp for comp in everything if comp.id == id6)

    pixel_result = compare(comp5, comp6)
    
    with open("example_pixel_comparison_receipt.json", "w") as f:
        json.dump(pixel_result, f, indent=2)



    # visualize the comparing pixels
    comparing_pixels = []
    p1 = next(comp for comp in everything if comp.id == id5)
    p2 = next(comp for comp in everything if comp.id == id6)
    comparing_pixels.append(p1.view)
    comparing_pixels.append(p2.view)

    plot_data(comparing_pixels)
