# from managers.arc_manager import ARCManager
# from pprint import pprint
# import os
# import json

# def id_to_json_path(id):
#     TASK_HEX_CODE = id[0]
#     PNUM = id[1]
#     GNUM = id[2]
#     ONUM = id[3]
#     XNUM = id[4]
#     TYP = id[5]

#     root = "memory/"

#     if TYP == "task" or TYP == "t":
#         return f"{root}TASK_nodes/TASK_{TASK_HEX_CODE}/TASK_property/TASK_{TASK_HEX_CODE}_property.json"
#     elif TYP == "pair" or TYP == "p":
#         return f"{root}TASK_nodes/TASK_{TASK_HEX_CODE}/PAIR_nodes/PAIR_{PNUM}/PAIR_property/PAIR_{PNUM}_property.json"
#     elif TYP == "grid" or TYP == "g":
#         return f"{root}TASK_nodes/TASK_{TASK_HEX_CODE}/PAIR_nodes/PAIR_{PNUM}/GRID_nodes/GRID_{GNUM}/GRID_property/GRID_{GNUM}_property.json"
#     elif TYP == "object" or TYP == "o":
#         return f"{root}TASK_nodes/TASK_{TASK_HEX_CODE}/PAIR_nodes/PAIR_{PNUM}/GRID_nodes/GRID_{GNUM}/OBJECT_nodes/OBJECT_{ONUM}/OBJECT_property/OBJECT_{ONUM}_property.json"
#     elif TYP == "pixel" or TYP == "x":
#         return f"{root}TASK_nodes/TASK_{TASK_HEX_CODE}/PAIR_nodes/PAIR_{PNUM}/GRID_nodes/GRID_{GNUM}/PIXEL_nodes/PIXEL_{XNUM}/PIXEL_property/PIXEL_{XNUM}_property.json"
#     else:
#         raise ValueError("Invalid type. Check the type.")

# def json_path_to_id(json_path):
#     root = "memory/"
#     if "TASK_property" in json_path:
#         return (json_path.split(root)[-1].split("/")[1].split("_")[-1], None, None, None, None, "task")
#     elif "PAIR_property" in json_path:
#         return (json_path.split(root)[-1].split("/")[1].split("_")[-1], json_path.split(root)[-1].split("/")[-3].split("_")[-1], None, None, None, "pair")
#     elif "GRID_property" in json_path:
#         return (json_path.split(root)[-1].split("/")[1].split("_")[-1], json_path.split(root)[-1].split("/")[-5].split("_")[-1], json_path.split(root)[-1].split("/")[-3].split("_")[-1], None, None, "grid")
#     elif "OBJECT_property" in json_path:
#         return (json_path.split(root)[-1].split("/")[1].split("_")[-1], json_path.split(root)[-1].split("/")[-7].split("_")[-1], json_path.split(root)[-1].split("/")[-5].split("_")[-1], json_path.split(root)[-1].split("/")[-3].split("_")[-1], None, "object")
#     elif "PIXEL_property" in json_path:
#         return (json_path.split(root)[-1].split("/")[1].split("_")[-1], json_path.split(root)[-1].split("/")[-7].split("_")[-1], json_path.split(root)[-1].split("/")[-5].split("_")[-1], None, json_path.split(root)[-1].split("/")[-3].split("_")[-1], "pixel")
#     else:
#         raise ValueError("Invalid json path. Check the json path.")
    
# def id_pair_to_comparison_path(id1, id2):
#     root = "memory/"
#     TASK_HEX_CODE = (id1[0], id2[0])
#     PNUM = (id1[1], id2[1])
#     GNUM = (id1[2], id2[2])
#     ONUM = (id1[3], id2[3])
#     XNUM = (id1[4], id2[4])
#     TYP = (id1[5], id2[5])

#     if TYP[0] == "task" or TYP[0] == "t":
#         return f"{root}TASK_edges/TASK_{TASK_HEX_CODE[0]}-TASK_{TASK_HEX_CODE[1]}.json"
#     elif TYP[0] == "pair" or TYP[0] == "p":
#         return f"{root}TASK_nodes/TASK_{TASK_HEX_CODE[0]}/PAIR_nodes/PAIR_{PNUM[0]}-PAIR_{PNUM[1]}.json"
#     elif TYP[0] == "grid" or TYP[0] == "g":
#         return f"{root}TASK_nodes/TASK_{TASK_HEX_CODE[0]}/PAIR_nodes/PAIR_{PNUM[0]}/GRID_edges/GRID_{GNUM[0]}-GRID_{GNUM[1]}.json"
#     elif TYP[0] == "object" or TYP[0] == "o":
#         return f"{root}TASK_nodes/TASK_{TASK_HEX_CODE[0]}/PAIR_nodes/PAIR_{PNUM[0]}/GRID_nodes/GRID_{GNUM[0]}/OBJECT_edges/OBJECT_{ONUM[0]}-OBJECT_{ONUM[1]}.json"
#     elif TYP[0] == "pixel" or TYP[0] == "x":
#         return f"{root}TASK_nodes/TASK_{TASK_HEX_CODE[0]}/PAIR_nodes/PAIR_{PNUM[0]}/GRID_nodes/GRID_{GNUM[0]}/PIXEL_edges/PIXEL_{XNUM[0]}-PIXEL_{XNUM[1]}.json"
#     else:
#         raise ValueError("Invalid type. Check the type.")

# def load_json_file(json_path):
#     if not os.path.exists(json_path):
#         raise FileNotFoundError(f"File not found: {json_path}")
#     with open(json_path, "r") as f:
#         return json.load(f)
    
# def compare(comp1, comp2, path=""):
#     result = {
#         "type": None,
#         "comp1": comp1,
#         "comp2": comp2,
#         "details": {}
#     }
    
#     # Handle different data types
#     if type(comp1) != type(comp2):
#         result["type"] = "DIFF"
#         return result
    
#     # Handle None values
#     if comp1 is None and comp2 is None:
#         result["type"] = "COMM"
#         return result
#     elif comp1 is None or comp2 is None:
#         result["type"] = "DIFF"
#         return result
    
#     # Handle primitive types (int, float, str, bool)
#     if isinstance(comp1, (int, float, str, bool)):
#         if comp1 == comp2:
#             result["type"] = "COMM"
#         else:
#             result["type"] = "DIFF"
#         return result
    
#     # Handle lists
#     if isinstance(comp1, list):
#         if len(comp1) != len(comp2):
#             result["type"] = "DIFF"
#             return result
        
#         # Compare each element in the list
#         list_results = []
#         all_common = True
#         for i, (item1, item2) in enumerate(zip(comp1, comp2)):
#             item_result = compare(item1, item2, f"{path}[{i}]")
#             list_results.append(item_result)
#             if item_result["type"] == "DIFF":
#                 all_common = False
        
#         result["type"] = "COMM" if all_common else "DIFF"
#         result["details"] = list_results
#         return result
    
#     # Handle dictionaries
#     if isinstance(comp1, dict):
#         # Get all unique keys from both dictionaries
#         all_keys = set(comp1.keys()) | set(comp2.keys())
        
#         if not all_keys:
#             # Both dictionaries are empty
#             result["type"] = "COMM"
#             return result
        
#         # Compare each key
#         key_results = {}
#         all_common = True
        
#         for key in all_keys:
#             key_path = f"{path}.{key}" if path else key
            
#             if key not in comp1:
#                 # Key missing in comp1
#                 key_results[key] = {
#                     "type": "DIFF",
#                     "comp1": None,
#                     "comp2": comp2[key],
#                     "details": {}
#                 }
#                 all_common = False
#             elif key not in comp2:
#                 # Key missing in comp2
#                 key_results[key] = {
#                     "type": "DIFF",
#                     "comp1": comp1[key],
#                     "comp2": None,
#                     "details": {}
#                 }
#                 all_common = False
#             else:
#                 # Key exists in both, compare values
#                 key_result = compare(comp1[key], comp2[key], key_path)
#                 key_results[key] = key_result
#                 if key_result["type"] == "DIFF":
#                     all_common = False
        
#         result["type"] = "COMM" if all_common else "DIFF"
#         result["details"] = key_results
#         return result
    
#     # Handle other types (tuples, sets, etc.)
#     try:
#         if comp1 == comp2:
#             result["type"] = "COMM"
#         else:
#             result["type"] = "DIFF"
#     except:
#         result["type"] = "DIFF"
    
#     return result


# def count_comm_in_category(category_data, count_leaf_nodes_only=False):
#     comm_count = 0
#     diff_count = 0
    
#     if isinstance(category_data, dict):
#         # If this has a type and no details (or empty details), it's a leaf node
#         if "type" in category_data and ("details" not in category_data or not category_data["details"]):
#             if category_data["type"] == "COMM":
#                 comm_count += 1
#             elif category_data["type"] == "DIFF":
#                 diff_count += 1
#         # If this has details, process the subcategories
#         elif "details" in category_data:
#             sub_details = category_data["details"]
#             if isinstance(sub_details, dict):
#                 for sub_key, sub_value in sub_details.items():
#                     if count_leaf_nodes_only:
#                         # Only count if this is a leaf node (has type but no details)
#                         if isinstance(sub_value, dict) and "type" in sub_value and ("details" not in sub_value or not sub_value["details"]):
#                             if sub_value["type"] == "COMM":
#                                 comm_count += 1
#                             elif sub_value["type"] == "DIFF":
#                                 diff_count += 1
#                     else:
#                         # Recursively count the subcategory
#                         sub_comm, sub_diff = count_comm_in_category(sub_value, count_leaf_nodes_only)
#                         comm_count += sub_comm
#                         diff_count += sub_diff
#             elif isinstance(sub_details, list):
#                 for item in sub_details:
#                     sub_comm, sub_diff = count_comm_in_category(item, count_leaf_nodes_only)
#                     comm_count += sub_comm
#                     diff_count += sub_diff
    
#     return comm_count, diff_count


# def get_comparison_data(comparison_result):
#     def count_comm_in_category(category_data, count_leaf_nodes_only=False):
#         comm_count = 0
#         diff_count = 0
        
#         if isinstance(category_data, dict):
#             # If this has a type and no details (or empty details), it's a leaf node
#             if "type" in category_data and ("details" not in category_data or not category_data["details"]):
#                 if category_data["type"] == "COMM":
#                     comm_count += 1
#                 elif category_data["type"] == "DIFF":
#                     diff_count += 1
#             # If this has details, process the subcategories
#             elif "details" in category_data:
#                 sub_details = category_data["details"]
#                 if isinstance(sub_details, dict):
#                     for sub_key, sub_value in sub_details.items():
#                         if count_leaf_nodes_only:
#                             # Only count if this is a leaf node (has type but no details)
#                             if isinstance(sub_value, dict) and "type" in sub_value and ("details" not in sub_value or not sub_value["details"]):
#                                 if sub_value["type"] == "COMM":
#                                     comm_count += 1
#                                 elif sub_value["type"] == "DIFF":
#                                     diff_count += 1
#                         else:
#                             # Recursively count the subcategory
#                             sub_comm, sub_diff = count_comm_in_category(sub_value, count_leaf_nodes_only)
#                             comm_count += sub_comm
#                             diff_count += sub_diff
#                 elif isinstance(sub_details, list):
#                     for item in sub_details:
#                         sub_comm, sub_diff = count_comm_in_category(item, count_leaf_nodes_only)
#                         comm_count += sub_comm
#                         diff_count += sub_diff
        
#         return comm_count, diff_count
    
#     def process_category_recursive(category_data):
#         result = {
#             "type": category_data.get("type", "UNKNOWN")
#         }
        
#         # Check if this category has deeper subcategories
#         has_deeper_subcategories = False
#         if isinstance(category_data, dict) and "details" in category_data:
#             sub_details = category_data["details"]
#             if isinstance(sub_details, dict):
#                 has_deeper_subcategories = any(
#                     isinstance(sub_value, dict) and "details" in sub_value and sub_value["details"]
#                     for sub_value in sub_details.values()
#                 )
        
#         # Calculate score
#         if has_deeper_subcategories:
#             # For categories with deeper subcategories, count only the immediate subcategories
#             comm_count, diff_count = count_comm_in_category(category_data, count_leaf_nodes_only=True)
            
#             # For categories with deeper subcategories, we need to count the immediate subcategories differently
#             if isinstance(category_data, dict) and "details" in category_data:
#                 sub_details = category_data["details"]
#                 if isinstance(sub_details, dict):
#                     comm_count = 0
#                     diff_count = 0
#                     for sub_key, sub_value in sub_details.items():
#                         if isinstance(sub_value, dict) and "type" in sub_value:
#                             if sub_value["type"] == "COMM":
#                                 comm_count += 1
#                             elif sub_value["type"] == "DIFF":
#                                 diff_count += 1
#         else:
#             # For regular categories, count all leaf nodes
#             comm_count, diff_count = count_comm_in_category(category_data)
        
#         total_count = comm_count + diff_count
#         result["score"] = f"{comm_count}/{total_count}"
        
#         # Process subcategories (renamed to category for unification)
#         if isinstance(category_data, dict) and "details" in category_data:
#             sub_details = category_data["details"]
#             if isinstance(sub_details, dict):
#                 result["category"] = {}
#                 # Sort subcategories for consistent ordering
#                 sorted_sub_items = sorted(sub_details.items(), key=lambda x: str(x[0]))
#                 for sub_key, sub_value in sorted_sub_items:
#                     result["category"][sub_key] = process_category_recursive(sub_value)
                
#                 # If category is empty (no subcategories), preserve comp1 and comp2
#                 if not result["category"] and isinstance(category_data, dict) and "comp1" in category_data and "comp2" in category_data:
#                     result["comp1"] = category_data["comp1"]
#                     result["comp2"] = category_data["comp2"]
#         else:
#             # If this is a leaf node (no details), preserve comp1 and comp2
#             if isinstance(category_data, dict) and "comp1" in category_data and "comp2" in category_data:
#                 result["comp1"] = category_data["comp1"]
#                 result["comp2"] = category_data["comp2"]
        
#         return result
    
#     # Process top-level categories
#     combined_data = {
#         "type": comparison_result.get("type", "UNKNOWN"),
#         "score": "0/0",  # Will be updated below
#         "category": {}
#     }
    
#     if isinstance(comparison_result, dict) and "details" in comparison_result:
#         details = comparison_result["details"]
#         if isinstance(details, dict):
#             # Count top-level categories
#             comm_categories = 0
#             total_categories = len(details)
#             for category_name, category_data in details.items():
#                 if isinstance(category_data, dict) and category_data.get("type") == "COMM":
#                     comm_categories += 1
            
#             combined_data["score"] = f"{comm_categories}/{total_categories}"
            
#             # Process each category
#             # Handle mixed key types (strings and integers) by converting all to strings for sorting
#             sorted_items = sorted(details.items(), key=lambda x: str(x[0]))
#             for category_name, category_data in sorted_items:
#                 combined_data["category"][category_name] = process_category_recursive(category_data)
    
#     return combined_data



# def save_comparison_result(comparison_result, output_path, id1=None, id2=None):
#     combined_data = get_comparison_data(comparison_result)
    
#     final_data = {
#         "id1": str(id1),
#         "id2": str(id2),
#         "result": combined_data
#     }

#     with open(output_path, 'w') as f:
#         json.dump(final_data, f, indent=2, default=str)
    
#     print(f"Combined comparison data saved to: {output_path}")

# def print_comparison_result(comparison_result):
#     print("=== Comparison Result and Scores ===")
#     # Count top-level categories
#     if isinstance(comparison_result, dict) and "details" in comparison_result:
#         details = comparison_result["details"]
#         if isinstance(details, dict):
#             comm_categories = 0
#             total_categories = len(details)
#             for category_name, category_data in details.items():
#                 if isinstance(category_data, dict) and category_data.get("type") == "COMM":
#                     comm_categories += 1
            
#             # Determine status and type
#             if comm_categories == total_categories:
#                 status = "✓"
#                 category_type = "COMM"
#             else:
#                 status = "✗"
#                 category_type = "DIFF"
            
#             print(f"{status}: {comm_categories}/{total_categories} {category_type}")
    
    
    
#     def print_category_scores_recursive(result_dict, indent=0):
#         """Recursively print category scores with indentation."""
#         if not isinstance(result_dict, dict) or "details" not in result_dict:
#             return
        
#         details = result_dict["details"]
#         if not isinstance(details, dict):
#             return
        
#         prefix = " " * 30 * indent  # 30 spaces per indentation level
        
#         # Sort category names for consistent output
#         # Handle mixed key types (strings and integers) by converting all to strings for sorting
#         sorted_items = sorted(details.items(), key=lambda x: str(x[0]))
#         for category_name, category_data in sorted_items:
#             # Check if this category has deeper subcategories
#             has_deeper_subcategories = False
#             if isinstance(category_data, dict) and "details" in category_data:
#                 sub_details = category_data["details"]
#                 if isinstance(sub_details, dict):
#                     has_deeper_subcategories = any(
#                         isinstance(sub_value, dict) and "details" in sub_value and sub_value["details"]
#                         for sub_value in sub_details.values()
#                     )
            
#             # Count COMM and DIFF in this category
#             if has_deeper_subcategories:
#                 # For categories with deeper subcategories, count only the immediate subcategories
#                 comm_count, diff_count = count_comm_in_category(category_data, count_leaf_nodes_only=True)
                
#                 # For categories with deeper subcategories, we need to count the immediate subcategories differently
#                 if isinstance(category_data, dict) and "details" in category_data:
#                     sub_details = category_data["details"]
#                     if isinstance(sub_details, dict):
#                         comm_count = 0
#                         diff_count = 0
#                         for sub_key, sub_value in sub_details.items():
#                             if isinstance(sub_value, dict) and "type" in sub_value:
#                                 if sub_value["type"] == "COMM":
#                                     comm_count += 1
#                                 elif sub_value["type"] == "DIFF":
#                                     diff_count += 1
#             else:
#                 # For regular categories, count all leaf nodes
#                 comm_count, diff_count = count_comm_in_category(category_data)
            
#             total_count = comm_count + diff_count
            
#             if total_count > 0:
#                 status = "✓" if category_data.get("type") == "COMM" else "✗"
#                 print(f"{prefix}{status} {category_name}: {comm_count}/{total_count} ({category_data.get('type', 'MIXED')})")
#             else:
#                 # No subcategories to count
#                 status = "✓" if category_data.get("type") == "COMM" else "✗"
#                 print(f"{prefix}{status} {category_name}: ({category_data.get('type', 'MIXED')})")
            
#             # Always print subcategories if they exist
#             if isinstance(category_data, dict) and "details" in category_data:
#                 sub_details = category_data["details"]
#                 if isinstance(sub_details, dict):
#                     print_category_scores_recursive(category_data, indent + 1)
    
#     # Start with 30 spaces indentation for all category scores
#     print_category_scores_recursive(comparison_result, indent=1)
#     print("=" * 30)

            
# if __name__ == "__main__":
#     # comparing from memory (.json)

#     TASK_HEX_CODE = "08ed6ac7"
#     ARCManager.from_hex_code(TASK_HEX_CODE)

#     pnum = (0, 0)
#     gnum = (0, 1)
#     onum = (1, 2)
#     xnum = (9, 0)
#     typ = "grid"
    
#     id1 = (TASK_HEX_CODE, pnum[0], gnum[0], onum[0], xnum[0], typ)
#     id2 = (TASK_HEX_CODE, pnum[1], gnum[1], onum[1], xnum[1], typ)
    
#     comp1 = load_json_file(id_to_json_path(id1))
#     comp2 = load_json_file(id_to_json_path(id2))
    
#     result = compare(comp1, comp2)

#     # Print the comparison score
#     print_comparison_result(result)
    
#     # Save to JSON file
#     output_path = f"comparison_result_{TASK_HEX_CODE}_{typ}.json"
#     save_comparison_result(result, output_path, id1, id2)
import os
import json


def shapes_are_equivalent(shape1, shape2):
    """
    Check if two shapes are equivalent considering rotations and reflections.
    Returns True if the shapes are the same after any rotation (0°, 90°, 180°, 270°) 
    or reflection (horizontal, vertical, diagonal, anti-diagonal).
    """
    if not shape1 or not shape2:
        return shape1 == shape2
    
    # First check if they're exactly the same
    if shape1 == shape2:
        return True
    
    # Check all rotations
    for rotation in [0, 90, 180, 270]:
        rotated_shape = rotate_shape(shape1, rotation)
        if rotated_shape == shape2:
            return True
    
    # Check all reflections
    for reflection in ['horizontal', 'vertical', 'diagonal', 'antidiagonal']:
        reflected_shape = reflect_shape(shape1, reflection)
        if reflected_shape == shape2:
            return True
        
        # Check combinations of rotation and reflection
        for rotation in [0, 90, 180, 270]:
            rotated_reflected = rotate_shape(reflected_shape, rotation)
            if rotated_reflected == shape2:
                return True
    
    return False

def rotate_shape(shape, degrees):
    """Rotate a 2D shape by the specified degrees (0, 90, 180, 270)."""
    if not shape or degrees == 0:
        return shape
    
    if degrees == 90:
        # 90 degrees clockwise: transpose then reverse each row
        return [list(row[::-1]) for row in zip(*shape)]
    elif degrees == 180:
        # 180 degrees: reverse rows then reverse each row
        return [row[::-1] for row in shape[::-1]]
    elif degrees == 270:
        # 270 degrees clockwise: reverse each row then transpose
        return [list(row) for row in zip(*[row[::-1] for row in shape])]
    
    return shape

def reflect_shape(shape, reflection_type):
    """Reflect a 2D shape along the specified axis."""
    if not shape:
        return shape
    
    if reflection_type == 'horizontal':
        # Flip horizontally (reverse each row)
        return [row[::-1] for row in shape]
    elif reflection_type == 'vertical':
        # Flip vertically (reverse rows)
        return shape[::-1]
    elif reflection_type == 'diagonal':
        # Reflect along main diagonal
        return [list(row) for row in zip(*shape)]
    elif reflection_type == 'antidiagonal':
        # Reflect along anti-diagonal
        return [list(row[::-1]) for row in zip(*shape)][::-1]
    
    return shape

def get_comparison_data(comparison_result):
    def count_comm_in_category(category_data, count_leaf_nodes_only=False):
        comm_count = 0
        diff_count = 0
        
        if isinstance(category_data, dict):
            # If this has a type and no details (or empty details), it's a leaf node
            if "type" in category_data and ("details" not in category_data or not category_data["details"]):
                if category_data["type"] == "COMM":
                    comm_count += 1
                elif category_data["type"] == "DIFF":
                    diff_count += 1
            # If this has details, process the subcategories
            elif "details" in category_data:
                sub_details = category_data["details"]
                if isinstance(sub_details, dict):
                    for sub_key, sub_value in sub_details.items():
                        if count_leaf_nodes_only:
                            # Only count if this is a leaf node (has type but no details)
                            if isinstance(sub_value, dict) and "type" in sub_value and ("details" not in sub_value or not sub_value["details"]):
                                if sub_value["type"] == "COMM":
                                    comm_count += 1
                                elif sub_value["type"] == "DIFF":
                                    diff_count += 1
                        else:
                            # Recursively count the subcategory
                            sub_comm, sub_diff = count_comm_in_category(sub_value, count_leaf_nodes_only)
                            comm_count += sub_comm
                            diff_count += sub_diff
                elif isinstance(sub_details, list):
                    for item in sub_details:
                        sub_comm, sub_diff = count_comm_in_category(item, count_leaf_nodes_only)
                        comm_count += sub_comm
                        diff_count += sub_diff
        
        return comm_count, diff_count
    
    def process_category_recursive(category_data):
        result = {
            "type": category_data.get("type", "UNKNOWN")
        }
        
        # Check if this category has deeper subcategories
        has_deeper_subcategories = False
        if isinstance(category_data, dict) and "details" in category_data:
            sub_details = category_data["details"]
            if isinstance(sub_details, dict):
                has_deeper_subcategories = any(
                    isinstance(sub_value, dict) and "details" in sub_value and sub_value["details"]
                    for sub_value in sub_details.values()
                )
        
        # Calculate score
        if has_deeper_subcategories:
            # For categories with deeper subcategories, count only the immediate subcategories
            comm_count, diff_count = count_comm_in_category(category_data, count_leaf_nodes_only=True)
            
            # For categories with deeper subcategories, we need to count the immediate subcategories differently
            if isinstance(category_data, dict) and "details" in category_data:
                sub_details = category_data["details"]
                if isinstance(sub_details, dict):
                    comm_count = 0
                    diff_count = 0
                    for sub_key, sub_value in sub_details.items():
                        if isinstance(sub_value, dict) and "type" in sub_value:
                            if sub_value["type"] == "COMM":
                                comm_count += 1
                            elif sub_value["type"] == "DIFF":
                                diff_count += 1
        else:
            # For regular categories, count all leaf nodes
            comm_count, diff_count = count_comm_in_category(category_data)
        
        total_count = comm_count + diff_count
        result["score"] = f"{comm_count}/{total_count}"
        
        # Process subcategories (renamed to category for unification)
        if isinstance(category_data, dict) and "details" in category_data:
            sub_details = category_data["details"]
            if isinstance(sub_details, dict):
                result["category"] = {}
                # Sort subcategories for consistent ordering
                sorted_sub_items = sorted(sub_details.items(), key=lambda x: str(x[0]))
                for sub_key, sub_value in sorted_sub_items:
                    result["category"][sub_key] = process_category_recursive(sub_value)
                
                # If category is empty (no subcategories), preserve comp1 and comp2
                if not result["category"] and isinstance(category_data, dict) and "comp1" in category_data and "comp2" in category_data:
                    result["comp1"] = category_data["comp1"]
                    result["comp2"] = category_data["comp2"]
        else:
            # If this is a leaf node (no details), preserve comp1 and comp2
            if isinstance(category_data, dict) and "comp1" in category_data and "comp2" in category_data:
                result["comp1"] = category_data["comp1"]
                result["comp2"] = category_data["comp2"]
        
        return result
    
    # Process top-level categories
    result = {
        "type": comparison_result.get("type", "UNKNOWN"),
        "score": "0/0",  # Will be updated below
        "category": {}
    }
    
    if isinstance(comparison_result, dict) and "details" in comparison_result:
        details = comparison_result["details"]
        if isinstance(details, dict):
            # Count top-level categories
            comm_categories = 0
            total_categories = len(details)
            for category_name, category_data in details.items():
                if isinstance(category_data, dict) and category_data.get("type") == "COMM":
                    comm_categories += 1
            
            result["score"] = f"{comm_categories}/{total_categories}"
            
            # Process each category
            # Handle mixed key types (strings and integers) by converting all to strings for sorting
            sorted_items = sorted(details.items(), key=lambda x: str(x[0]))
            for category_name, category_data in sorted_items:
                result["category"][category_name] = process_category_recursive(category_data)
    
    return result

def compare_nested_json(comp1, comp2, path=""):
    result = {
        "type": None,
        "comp1": comp1,
        "comp2": comp2,
        "details": {}
    }
    
    # Handle different data types
    if type(comp1) != type(comp2):
        result["type"] = "DIFF"
        return result
    
    # Handle None values
    if comp1 is None and comp2 is None:
        result["type"] = "COMM"
        return result
    elif comp1 is None or comp2 is None:
        result["type"] = "DIFF"
        return result
    
    # Handle primitive types (int, float, str, bool)
    if isinstance(comp1, (int, float, str, bool)):
        if comp1 == comp2:
            result["type"] = "COMM"
        else:
            result["type"] = "DIFF"
        return result
    
    # Handle lists
    if isinstance(comp1, list):
        # Check if both lists have the same length (dimensions)
        if len(comp1) != len(comp2):
            result["type"] = "DIFF"
            result["comp1"] = comp1
            result["comp2"] = comp2
            result["details"] = {}
            return result
        
        # Check if lists are 2D (contain other lists)
        is_2d = any(isinstance(item, list) for item in comp1) or any(isinstance(item, list) for item in comp2)
        
        if is_2d:
            # Special handling for shape comparison - check if this is a shape field
            if path.endswith("shape") or "shape" in path:
                # Use rotation and reflection invariant comparison for shapes
                if shapes_are_equivalent(comp1, comp2):
                    result["type"] = "COMM"
                else:
                    result["type"] = "DIFF"
            else:
                # Grid contents 등 2D 리스트: 픽셀/셀 단위 정확 비교 (순서 무시 set 비교 시 다른 그리드가 COMM으로 나오는 버그 방지)
                all_common = True
                if len(comp1) != len(comp2):
                    all_common = False
                else:
                    for i in range(len(comp1)):
                        sublist1, sublist2 = comp1[i], comp2[i]
                        if not isinstance(sublist1, list) or not isinstance(sublist2, list):
                            all_common = False
                            break
                        if len(sublist1) != len(sublist2):
                            all_common = False
                            break
                        for j in range(len(sublist1)):
                            if sublist1[j] != sublist2[j]:
                                all_common = False
                                break
                        if not all_common:
                            break
                result["type"] = "COMM" if all_common else "DIFF"
        else:
            # For 1D lists, check if both lists have the same set of elements
            if set(comp1) == set(comp2):
                result["type"] = "COMM"
            else:
                result["type"] = "DIFF"
        
        result["comp1"] = comp1
        result["comp2"] = comp2
        result["details"] = {}
        return result
    
    # Handle dictionaries
    if isinstance(comp1, dict):
        # Get all unique keys from both dictionaries
        all_keys = set(comp1.keys()) | set(comp2.keys())
        
        if not all_keys:
            # Both dictionaries are empty
            result["type"] = "COMM"
            return result
        
        # Compare each key
        key_results = {}
        all_common = True
        
        for key in all_keys:
            key_path = f"{path}.{key}" if path else key
            
            if key not in comp1:
                # Key missing in comp1
                key_results[key] = {
                    "type": "DIFF",
                    "comp1": None,
                    "comp2": comp2[key],
                    "details": {}
                }
                all_common = False
            elif key not in comp2:
                # Key missing in comp2
                key_results[key] = {
                    "type": "DIFF",
                    "comp1": comp1[key],
                    "comp2": None,
                    "details": {}
                }
                all_common = False
            else:
                # Key exists in both, compare values
                key_result = compare_nested_json(comp1[key], comp2[key], key_path)
                key_results[key] = key_result
                if key_result["type"] == "DIFF":
                    all_common = False
        
        result["type"] = "COMM" if all_common else "DIFF"
        result["details"] = key_results
        return result
    
    # Handle other types (tuples, sets, etc.)
    try:
        if comp1 == comp2:
            result["type"] = "COMM"
        else:
            result["type"] = "DIFF"
    except:
        result["type"] = "DIFF"
    
    return result

def compare(comp1, comp2, save=True, label1=None, label2=None):
    """
    label1, label2: optional T,P,G,O,X 형식 레이블 (예: P0G0, P1G1). 저장 시 final_data에 포함.
    """
    id1 = get_component_full_id(comp1)
    id2 = get_component_full_id(comp2)
    path =""

    raw_result = compare_nested_json(comp1.property, comp2.property, path)
    processed_result = get_comparison_data(raw_result)

    final_data = {
        "id1": str(id1),
        "id2": str(id2),
        "result": processed_result
    }
    if label1 is not None:
        final_data["label1"] = label1
    if label2 is not None:
        final_data["label2"] = label2

    if save:
        # label1, label2가 있으면 task 노드 바로 아래 E_P0G0-P1G0.json 형식으로 저장 (PAIR 간 비교)
        if label1 is not None and label2 is not None:
            from .memory_paths import edge_task_level_comparison_path
            task_hex = id1.split(".")[0]
            output_path = edge_task_level_comparison_path(task_hex, label1, label2)
        else:
            score = 0
            if "score" in processed_result:
                try:
                    score = int(processed_result["score"].split("/")[0])
                except Exception:
                    score = 0
            output_path = id_pair_to_comparison_path(id1, id2, score)
        save_comparison_result(final_data, output_path)
        final_data["saved_path"] = output_path

        return final_data

    return final_data





def id_to_json_path(id):
    # id는 경로 문자열 (예: "007bbfb7.PAIR_nodes.0"). 반환 경로: memory/N_T{hex}/E_T{hex}.json 등
    from .memory_paths import (
        task_property_path,
        pair_property_path,
        grid_property_path,
        object_property_path,
        pixel_property_path,
        pixel_under_object_property_path,
    )
    path_parts = id.split('.')

    if len(path_parts) == 1:
        task_hex = path_parts[0]
        return task_property_path(task_hex)
    elif len(path_parts) == 3 and path_parts[1] == "PAIR_nodes":
        task_hex, pair_num = path_parts[0], path_parts[2]
        return pair_property_path(task_hex, int(pair_num))
    elif len(path_parts) == 5 and path_parts[1] == "PAIR_nodes" and path_parts[3] == "GRID_nodes":
        task_hex, pair_num, grid_num = path_parts[0], path_parts[2], path_parts[4]
        return grid_property_path(task_hex, int(pair_num), int(grid_num))
    elif len(path_parts) == 7 and path_parts[1] == "PAIR_nodes" and path_parts[3] == "GRID_nodes" and path_parts[5] == "OBJECT_nodes":
        task_hex, pair_num, grid_num, obj_num = path_parts[0], path_parts[2], path_parts[4], path_parts[6]
        return object_property_path(task_hex, int(pair_num), 'G', int(grid_num), int(obj_num))
    elif len(path_parts) == 7 and path_parts[1] == "PAIR_nodes" and path_parts[3] == "GRID_nodes" and path_parts[5] == "PIXEL_nodes":
        task_hex, pair_num, grid_num, pixel_num = path_parts[0], path_parts[2], path_parts[4], path_parts[6]
        return pixel_property_path(task_hex, int(pair_num), 'G', int(grid_num), int(pixel_num))
    elif len(path_parts) == 9 and path_parts[1] == "PAIR_nodes" and path_parts[3] == "GRID_nodes" and path_parts[5] == "OBJECT_nodes" and path_parts[7] == "PIXEL_nodes":
        task_hex, pair_num, grid_num, obj_num, pixel_num = path_parts[0], path_parts[2], path_parts[4], path_parts[6], path_parts[8]
        return pixel_under_object_property_path(task_hex, int(pair_num), 'G', int(grid_num), int(obj_num), int(pixel_num))
    else:
        raise ValueError(f"Invalid id format: {id}")

def json_path_to_id(json_path):
    # New path format: memory/N_T{hex}/E_T{hex}.json, memory/N_T{hex}/N_P0/E_P0.json, ...
    from .memory_paths import MEMORY_ROOT
    path_parts = json_path.split(MEMORY_ROOT)[-1].rstrip("/").split("/")

    def _task_hex():
        for p in path_parts:
            if p.startswith("N_T"):
                return p[3:]
        return None

    def _grid_num(part):
        if part.startswith("N_G"):
            return part[3:]
        return None

    if not path_parts or not path_parts[0].startswith("N_T"):
        raise ValueError(f"Invalid json path: {json_path}")

    task_hex = _task_hex()
    if len(path_parts) == 2 and path_parts[1].startswith("E_T"):
        return task_hex
    if len(path_parts) >= 4 and path_parts[1].startswith("N_P") and path_parts[3].startswith("E_P"):
        pair_num = path_parts[1][3:]
        return f"{task_hex}.PAIR_nodes.{pair_num}"
    if len(path_parts) >= 6 and path_parts[3].startswith("N_G") and path_parts[5].startswith("E_G"):
        pair_num = path_parts[1][3:]
        grid_num = path_parts[3][3:]
        return f"{task_hex}.PAIR_nodes.{pair_num}.GRID_nodes.{grid_num}"
    if len(path_parts) >= 8 and path_parts[5].startswith("N_O") and path_parts[7].startswith("E_O"):
        pair_num = path_parts[1][3:]
        grid_num = _grid_num(path_parts[3])
        if grid_num is None:
            raise ValueError(f"Invalid json path: {json_path}")
        obj_num = path_parts[5][3:]
        return f"{task_hex}.PAIR_nodes.{pair_num}.GRID_nodes.{grid_num}.OBJECT_nodes.{obj_num}"
    if len(path_parts) >= 8 and path_parts[5].startswith("N_X") and path_parts[7].startswith("E_X"):
        pair_num = path_parts[1][3:]
        grid_num = _grid_num(path_parts[3])
        if grid_num is None:
            raise ValueError(f"Invalid json path: {json_path}")
        pixel_num = path_parts[5][3:]
        return f"{task_hex}.PAIR_nodes.{pair_num}.GRID_nodes.{grid_num}.PIXEL_nodes.{pixel_num}"
    if len(path_parts) >= 10 and path_parts[7].startswith("N_X") and path_parts[9].startswith("E_X"):
        pair_num = path_parts[1][3:]
        grid_num = _grid_num(path_parts[3])
        if grid_num is None:
            raise ValueError(f"Invalid json path: {json_path}")
        obj_num = path_parts[5][3:]
        pixel_num = path_parts[7][3:]
        return f"{task_hex}.PAIR_nodes.{pair_num}.GRID_nodes.{grid_num}.OBJECT_nodes.{obj_num}.PIXEL_nodes.{pixel_num}"
    raise ValueError(f"Invalid json path: {json_path}")
    
def id_pair_to_comparison_path(id1, id2, score=0):
    # Comparison edge paths: memory/N_T{hex}/E_P0-P1.json, E_G0-G1.json, etc.
    from .memory_paths import (
        edge_task_comparison_path,
        edge_pair_comparison_path,
        edge_grid_comparison_path,
        edge_object_comparison_path,
        edge_pixel_comparison_path_grid,
        edge_pixel_comparison_path_object,
    )
    task_hex1 = id1.split('.')[0]
    path_parts1 = id1.split('.')
    path_parts2 = id2.split('.')

    if len(path_parts1) == 1:
        return edge_task_comparison_path(task_hex1, path_parts2[0])
    elif len(path_parts1) == 3 and path_parts1[1] == "PAIR_nodes":
        pair_num1, pair_num2 = path_parts1[2], path_parts2[2]
        return edge_pair_comparison_path(task_hex1, pair_num1, pair_num2, score)
    elif len(path_parts1) == 5 and path_parts1[1] == "PAIR_nodes" and path_parts1[3] == "GRID_nodes":
        pair_num1 = path_parts1[2]
        grid_num1, grid_num2 = path_parts1[4], path_parts2[4]
        return edge_grid_comparison_path(task_hex1, pair_num1, grid_num1, grid_num2, score)
    elif len(path_parts1) == 7 and path_parts1[1] == "PAIR_nodes" and path_parts1[3] == "GRID_nodes" and path_parts1[5] == "OBJECT_nodes":
        pair_num1, grid_num1 = path_parts1[2], path_parts1[4]
        obj_num1, obj_num2 = path_parts1[6], path_parts2[6]
        return edge_object_comparison_path(task_hex1, pair_num1, grid_num1, obj_num1, obj_num2, score)
    elif len(path_parts1) == 7 and path_parts1[1] == "PAIR_nodes" and path_parts1[3] == "GRID_nodes" and path_parts1[5] == "PIXEL_nodes":
        pair_num1, grid_num1 = path_parts1[2], path_parts1[4]
        pixel_num1, pixel_num2 = path_parts1[6], path_parts2[6]
        return edge_pixel_comparison_path_grid(task_hex1, pair_num1, grid_num1, pixel_num1, pixel_num2, score)
    elif len(path_parts1) == 9 and path_parts1[1] == "PAIR_nodes" and path_parts1[3] == "GRID_nodes" and path_parts1[5] == "OBJECT_nodes" and path_parts1[7] == "PIXEL_nodes":
        pair_num1, grid_num1, obj_num1 = path_parts1[2], path_parts1[4], path_parts1[6]
        pixel_num1, pixel_num2 = path_parts1[8], path_parts2[8]
        return edge_pixel_comparison_path_object(task_hex1, pair_num1, grid_num1, obj_num1, pixel_num1, pixel_num2, score)
    else:
        raise ValueError(f"Invalid id format: {id1} or {id2}")


def get_component_full_id(component):
    """Generate consistent dot-separated ID for all component types"""
    if component.type == "task":
        return component.hex_code
    elif component.type == "pair":
        # Handle tuple id format for pairs
        if isinstance(component.id, tuple) and len(component.id) >= 6:
            pair_num = component.id[1]  # Extract pair number from tuple
        else:
            pair_num = component.id
        return f"{component.parent.hex_code}.PAIR_nodes.{pair_num}"
    elif component.type == "grid":
        # Handle tuple id format for grids
        if isinstance(component.id, tuple) and len(component.id) >= 6:
            grid_num = component.id[2]  # Extract grid number from tuple
        else:
            grid_num = component.id
        return f"{component.parent[0].parent.hex_code}.PAIR_nodes.{component.parent[0].id}.GRID_nodes.{grid_num}"
    elif component.type == "object":
        # Handle tuple id format for objects
        if isinstance(component.id, tuple) and len(component.id) >= 6:
            obj_num = component.id[3]  # Extract object number from tuple
        else:
            obj_num = component.id
        return f"{component.parent[0].parent[0].parent.hex_code}.PAIR_nodes.{component.parent[0].parent[0].id}.GRID_nodes.{component.parent[0].id}.OBJECT_nodes.{obj_num}"
    elif component.type == "pixel":
        # Handle tuple id format for pixels
        if isinstance(component.id, tuple) and len(component.id) >= 6:
            pixel_num = component.id[4]  # Extract pixel number from tuple
        else:
            pixel_num = component.id
        return f"{component.parent[0].parent[0].parent.hex_code}.PAIR_nodes.{component.parent[0].parent[0].id}.GRID_nodes.{component.parent[0].id}.PIXEL_nodes.{pixel_num}"
    else:
        raise ValueError(f"Invalid component type: {component.type}")

def load_json_file(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"File not found: {json_path}")
    with open(json_path, "r") as f:
        return json.load(f)

def save_comparison_result(data, output_path):
    import os
    
    # Create directory structure if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Also create the score-based subfolder structure if it's a comparison result
    if "result" in data and "score" in data["result"]:
        try:
            score = int(data["result"]["score"].split("/")[0])
            # Extract the base path (without the score folder)
            path_parts = output_path.split('/')
            if len(path_parts) >= 2:
                # Find the score folder in the path and create the full structure
                base_path = '/'.join(path_parts[:-1])  # Remove the filename
                os.makedirs(base_path, exist_ok=True)
        except:
            pass  # If score extraction fails, just use the original path
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    # print(f"Comparison result saved to: {output_path}") # Uncomment to print the output path

            


if __name__ == "__main__":
    from pprint import pprint
    from managers.arc_manager import ARCManager

    # comparing from memory (.json)
    TASK_HEX_CODE = "08ed6ac7"
    task = ARCManager.from_hex_code(TASK_HEX_CODE)

    # 새로운 경로 문자열 기반 id 사용
    input_grid_id = f"{TASK_HEX_CODE}.PAIR_nodes.0.GRID_nodes.0"
    output_grid_id = f"{TASK_HEX_CODE}.PAIR_nodes.0.GRID_nodes.1"
    
    # component 객체 가져오기
    input_grid = task.example_pairs[0].input_grid
    output_grid = task.example_pairs[0].output_grid

    # 비교할 component 선택 (예: grid)
    comp1 = input_grid
    comp2 = output_grid

    # 비교 실행
    comparison_result = compare(comp1, comp2, save=False)

    print("=== Processed Comparison Result ===")
    pprint(comparison_result)

    # 결과를 JSON 파일로 저장
    with open(f"comparison_result_{TASK_HEX_CODE}_grid.json", "w") as f:
        json.dump(comparison_result, f, indent=2, default=str)
