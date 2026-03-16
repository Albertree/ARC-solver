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


def _is_relation_result(d):
    """True if d is a relation result dict (has type, score, category per ARCKG spec)."""
    return (
        isinstance(d, dict)
        and "type" in d
        and "score" in d
        and "category" in d
    )


def _compare_scalar(v1, v2):
    """Return raw comparison node for two scalar values."""
    return {
        "type": "COMM" if v1 == v2 else "DIFF",
        "comp1": v1,
        "comp2": v2,
        "details": {},
    }


def compare_relation_results(r1, r2, prefix="result"):
    """
    Compare two relation result dicts (type, score, category). Returns raw tree
    (type, comp1, comp2, details) with dot-notation keys so get_comparison_data can process it.
    """
    details = {}
    # Compare type
    t1, t2 = r1.get("type"), r2.get("type")
    details[f"{prefix}.type"] = _compare_scalar(t1, t2)
    # Compare score
    s1, s2 = r1.get("score"), r2.get("score")
    details[f"{prefix}.score"] = _compare_scalar(s1, s2)
    # Compare category (recurse)
    c1, c2 = r1.get("category", {}), r2.get("category", {})
    all_keys = set(c1.keys()) | set(c2.keys())
    cat_details = {}
    for k in sorted(all_keys, key=str):
        v1 = c1.get(k) if isinstance(c1, dict) else None
        v2 = c2.get(k) if isinstance(c2, dict) else None
        if v1 is None or v2 is None:
            cat_details[k] = {"type": "DIFF", "comp1": v1, "comp2": v2, "details": {}}
        elif _is_relation_result(v1) and _is_relation_result(v2):
            sub = compare_relation_results(v1, v2, prefix=k)
            cat_details[k] = sub
        else:
            # Leaf or mixed: treat as scalar/struct via compare_nested_json
            raw = compare_nested_json(v1, v2, path=k)
            cat_details[k] = raw
    # Category type must match score: COMM iff all sub-items are COMM (so score n/n => type COMM)
    sub_results = [d for d in cat_details.values() if isinstance(d, dict) and "type" in d]
    category_type = (
        "COMM"
        if (not sub_results or all(d.get("type") == "COMM" for d in sub_results))
        else "DIFF"
    )
    details[f"{prefix}.category"] = {
        "type": category_type,
        "comp1": c1,
        "comp2": c2,
        "details": cat_details,
    }
    n_comm = sum(1 for d in details.values() if isinstance(d, dict) and d.get("type") == "COMM")
    n_total = len(details)
    return {
        "type": "COMM" if n_comm == n_total else "DIFF",
        "comp1": r1,
        "comp2": r2,
        "details": details,
    }


def compare(comp1, comp2, save=True, label1=None, label2=None, edge_id1=None, edge_id2=None, task_hex=None):
    """
    Unified compare: components (0/1차) or relation result dicts (2차+).
    - Components: id1/id2 = node ID (T{hex}.P{p}.G{g}...), edge_id = E_{short1}-{short2}, order=1.
    - Relation dicts: id1/id2 = edge_id1/edge_id2 (e.g. E_P0G0X6-P0G0X7), edge_id = 2nd-order E_(E_...)-(E_...), order=2.
    label1, label2: optional labels (e.g. P0G0, P1G1) for task-level path when both given.
    task_hex: optional; for 2nd-order+, used to compute lca_node_id from edge_id1/edge_id2 (hex only, no T prefix).
    """
    # Detect input type: component (has .property) vs relation result dict (type/score/category)
    is_relation = _is_relation_result(comp1) and _is_relation_result(comp2)
    if is_relation:
        raw_result = compare_relation_results(comp1, comp2, prefix="result")
        id1 = edge_id1 if edge_id1 is not None else "E_unknown1"
        id2 = edge_id2 if edge_id2 is not None else "E_unknown2"
        edge_id_2nd = f"E_({id1})-({id2})" if id1.startswith("E_") and id2.startswith("E_") else f"E_{id1}-{id2}"
        order = 2
        if task_hex and edge_id1 and edge_id2:
            lca_id = lca_node_id_from_edge_ids(edge_id1, edge_id2, task_hex)
        else:
            lca_id = None
    else:
        id1 = get_component_full_id(comp1)
        id2 = get_component_full_id(comp2)
        raw_result = compare_nested_json(comp1.property, comp2.property, "")
        edge_id_2nd = build_edge_id_1order(id1, id2)
        order = 1
        lca_id = lca_node_id(id1, id2)

    processed_result = get_comparison_data(raw_result)
    # Key order: id1, id2, lca_node_id, edge_id, order, result (then optional label1, label2, saved_path)
    final_data = {
        "id1": str(id1),
        "id2": str(id2),
        "lca_node_id": lca_id,
        "edge_id": edge_id_2nd,
        "order": order,
        "result": processed_result,
    }
    if label1 is not None:
        final_data["label1"] = label1
    if label2 is not None:
        final_data["label2"] = label2

    if save:
        output_path = None
        if label1 is not None and label2 is not None and not is_relation:
            from .memory_paths import edge_task_level_comparison_path
            task_hex = id1.split(".")[0]
            if task_hex.startswith("T"):
                task_hex = task_hex[1:]
            output_path = edge_task_level_comparison_path(task_hex, label1, label2)
        elif not is_relation:
            output_path = id_pair_to_comparison_path(id1, id2)
        # 2nd-order: save only if edge_path_for_2order is implemented and lca_id available; else skip
        if output_path is not None:
            save_comparison_result(final_data, output_path)
            final_data["saved_path"] = output_path

    return final_data





def _parse_spec_node_id(node_id):
    """Parse spec node ID T{hex}.P{p}.G{g}.O{o}.X{x} -> (hex, pair, grid, obj, pixel_under_obj, pixel_under_grid)."""
    parts = node_id.split(".")
    if not parts or not parts[0].startswith("T"):
        return None
    hex_code = parts[0][1:]
    pair = grid = obj = pixel_obj = pixel_grid = None
    i = 1
    if i < len(parts) and parts[i].startswith("P"):
        _p = parts[i][1:]
        pair = int(_p) if _p.isdigit() else _p
        i += 1
    if i < len(parts) and parts[i].startswith("G"):
        grid = int(parts[i][1:])
        i += 1
    if i < len(parts) and parts[i].startswith("O"):
        obj = int(parts[i][1:])
        i += 1
    if i < len(parts) and parts[i].startswith("X"):
        if obj is not None:
            pixel_obj = int(parts[i][1:])
        else:
            pixel_grid = int(parts[i][1:])
    return (hex_code, pair, grid, obj, pixel_obj, pixel_grid)


def id_to_json_path(id):
    """Node ID (spec format T{hex}.P{p}.G{g}...) -> property file path."""
    from .memory_paths import (
        task_property_path,
        pair_property_path,
        grid_property_path,
        object_property_path,
        pixel_property_path,
        pixel_under_object_property_path,
    )
    parsed = _parse_spec_node_id(id)
    if parsed is None:
        raise ValueError(f"Invalid id format: {id}")
    hex_code, pair, grid, obj, pixel_obj, pixel_grid = parsed
    if pair is None:
        return task_property_path(hex_code)
    if grid is None:
        return pair_property_path(hex_code, pair)
    if obj is None and pixel_grid is None:
        return grid_property_path(hex_code, pair, grid)
    if obj is not None and pixel_obj is None:
        return object_property_path(hex_code, pair, "G", grid, obj)
    if obj is not None and pixel_obj is not None:
        return pixel_under_object_property_path(hex_code, pair, "G", grid, obj, pixel_obj)
    return pixel_property_path(hex_code, pair, "G", grid, pixel_grid)

def json_path_to_id(json_path):
    """Property file path -> node ID in spec format T{hex}.P{p}.G{g}.O{o}.X{x}."""
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

    hex_code = _task_hex()
    prefix = f"T{hex_code}"
    if len(path_parts) == 2 and path_parts[1].startswith("E_T"):
        return prefix
    if len(path_parts) >= 4 and path_parts[1].startswith("N_P") and path_parts[3].startswith("E_P"):
        pair_num = path_parts[1][3:]
        return f"{prefix}.P{pair_num}"
    if len(path_parts) >= 6 and path_parts[3].startswith("N_G") and path_parts[5].startswith("E_G"):
        pair_num = path_parts[1][3:]
        grid_num = path_parts[3][3:]
        return f"{prefix}.P{pair_num}.G{grid_num}"
    if len(path_parts) >= 8 and path_parts[5].startswith("N_O") and path_parts[7].startswith("E_O"):
        pair_num = path_parts[1][3:]
        grid_num = _grid_num(path_parts[3])
        if grid_num is None:
            raise ValueError(f"Invalid json path: {json_path}")
        obj_num = path_parts[5][3:]
        return f"{prefix}.P{pair_num}.G{grid_num}.O{obj_num}"
    if len(path_parts) >= 8 and path_parts[5].startswith("N_X") and path_parts[7].startswith("E_X"):
        pair_num = path_parts[1][3:]
        grid_num = _grid_num(path_parts[3])
        if grid_num is None:
            raise ValueError(f"Invalid json path: {json_path}")
        pixel_num = path_parts[5][3:]
        return f"{prefix}.P{pair_num}.G{grid_num}.X{pixel_num}"
    if len(path_parts) >= 10 and path_parts[7].startswith("N_X") and path_parts[9].startswith("E_X"):
        pair_num = path_parts[1][3:]
        grid_num = _grid_num(path_parts[3])
        if grid_num is None:
            raise ValueError(f"Invalid json path: {json_path}")
        obj_num = path_parts[5][3:]
        pixel_num = path_parts[7][3:]
        return f"{prefix}.P{pair_num}.G{grid_num}.O{obj_num}.X{pixel_num}"
    raise ValueError(f"Invalid json path: {json_path}")
    
def id_pair_to_comparison_path(id1, id2, score=0):
    """Comparison edge path from two node IDs (spec format). LCA folder + E_{short1}-{short2}.json. score ignored (filename = edge_id)."""
    if _parse_spec_node_id(id1) is None or _parse_spec_node_id(id2) is None:
        raise ValueError(f"Invalid id format: {id1} or {id2}")
    edge_id = build_edge_id_1order(id1, id2)
    return edge_path_for_comparison(id1, id2, edge_id)


def _parent_hex(component):
    """Get hex_code from component or its parent (parent may be list or single)."""
    if getattr(component, "hex_code", None):
        return component.hex_code
    p = getattr(component, "parent", None)
    if p is None:
        return None
    if isinstance(p, list):
        p = p[0] if p else None
    return getattr(p, "hex_code", None) if p else None


def _node_id_spec_parts(component):
    """Return (hex, parts) for spec node ID: parts = ['P0','G0','O1','X6'] etc."""
    if component.type == "task":
        return (component.hex_code, [])
    hex_code = _parent_hex(component) or ""
    if component.type == "pair":
        pair_num = component.id[1] if isinstance(component.id, tuple) and len(component.id) >= 6 else component.id
        return (hex_code, [f"P{pair_num}"])
    elif component.type == "grid":
        grid_num = component.id[2] if isinstance(component.id, tuple) and len(component.id) >= 6 else component.id
        parent = component.parent[0] if isinstance(component.parent, list) else component.parent
        p_id = parent.id
        pair_num = p_id[1] if isinstance(p_id, tuple) and len(p_id) >= 6 else p_id
        h = _parent_hex(parent) or hex_code
        return (h, [f"P{pair_num}", f"G{grid_num}"])
    elif component.type == "object":
        obj_num = component.id[3] if isinstance(component.id, tuple) and len(component.id) >= 6 else component.id
        p_top = component.parent[0] if isinstance(component.parent, list) else component.parent
        p_mid = p_top.parent[0] if isinstance(p_top.parent, list) else p_top.parent
        pair_num = p_mid.id[1] if isinstance(p_mid.id, tuple) and len(p_mid.id) >= 6 else p_mid.id
        grid_num = p_top.id[2] if isinstance(p_top.id, tuple) and len(p_top.id) >= 6 else p_top.id
        h = _parent_hex(p_mid) or hex_code
        return (h, [f"P{pair_num}", f"G{grid_num}", f"O{obj_num}"])
    elif component.type == "pixel":
        pixel_num = component.id[4] if isinstance(component.id, tuple) and len(component.id) >= 6 else component.id
        p_top = component.parent[0] if isinstance(component.parent, list) else component.parent
        p_mid = p_top.parent[0] if isinstance(p_top.parent, list) else p_top.parent
        pair_num = p_mid.id[1] if isinstance(p_mid.id, tuple) and len(p_mid.id) >= 6 else p_mid.id
        grid_num = p_top.id[2] if isinstance(p_top.id, tuple) and len(p_top.id) >= 6 else p_top.id
        h = _parent_hex(p_mid) or hex_code
        if getattr(p_top, "type", None) == "object":
            obj_num = p_top.id[3] if isinstance(p_top.id, tuple) and len(p_top.id) >= 6 else p_top.id
            return (h, [f"P{pair_num}", f"G{grid_num}", f"O{obj_num}", f"X{pixel_num}"])
        return (h, [f"P{pair_num}", f"G{grid_num}", f"X{pixel_num}"])
    raise ValueError(f"Invalid component type: {component.type}")


def get_component_full_id(component):
    """Node ID in spec format: T{hex}.P{p}.G{g}.O{o}.X{x} (ARCKG_structure_spec)."""
    hex_code, parts = _node_id_spec_parts(component)
    if not parts:
        return f"T{hex_code}"
    return f"T{hex_code}." + ".".join(parts)


def node_id_to_short_name(node_id):
    """T08ed6ac7.P0.G0.X6 -> P0G0X6 (for use in E_ edge filenames)."""
    if not node_id or not isinstance(node_id, str):
        return node_id
    if node_id.startswith("T") and "." in node_id:
        rest = node_id.split(".", 1)[1]
        return rest.replace(".", "")
    if node_id.startswith("T"):
        return ""  # task only
    return node_id.replace(".", "")


def _short_name_to_node_id(short, task_hex):
    """Convert short name (e.g. P0G0X6) to full node ID T{task_hex}.P0.G0.X6."""
    import re
    parts = re.findall(r"[PGOX]\d+", short)
    if not parts:
        return None
    return f"T{task_hex}." + ".".join(parts)


def _parse_edge_id_1st(edge_id):
    """Parse 1st-order edge ID E_A-B -> (short_a, short_b). Returns None if not 1st order."""
    if not edge_id or not isinstance(edge_id, str) or not edge_id.startswith("E_"):
        return None
    s = edge_id[2:]
    if ")-(" in s or s.startswith("("):
        return None  # 2nd order or higher
    if "-" in s:
        a, b = s.split("-", 1)
        return (a.strip(), b.strip())
    return None


def _parse_edge_id_2nd(edge_id):
    """Parse 2nd-order edge ID E_(E_A-B)-(E_C-D) -> (inner1, inner2). Returns None if not 2nd order."""
    if not edge_id or not edge_id.startswith("E_("):
        return None
    s = edge_id[2:]  # "(E_A-B)-(E_C-D)"
    if not s.startswith("(") or ")-(" not in s:
        return None
    # s[1:] = "E_A-B)-(E_C-D)", split by ")-(" -> ["E_A-B", "E_C-D)"]
    parts = s[1:].split(")-(")
    if len(parts) != 2:
        return None
    inner1, inner2 = parts[0], parts[1].rstrip(")")
    return (inner1, inner2)


def lca_node_id_from_edge_ids(edge_id1, edge_id2, task_hex):
    """
    LCA node ID for two edges (1st or 2nd order). task_hex is the task hex (no T prefix).
    For 1st-order edges, LCA of the four nodes; for 2nd-order, LCA of the two edges' LCAs.
    """
    def lca_of_edge(eid):
        parsed_1st = _parse_edge_id_1st(eid)
        if parsed_1st:
            a, b = parsed_1st
            n1 = _short_name_to_node_id(a, task_hex)
            n2 = _short_name_to_node_id(b, task_hex)
            if n1 and n2:
                return lca_node_id(n1, n2)
        parsed_2nd = _parse_edge_id_2nd(eid)
        if parsed_2nd:
            inner1, inner2 = parsed_2nd
            l1 = lca_of_edge(inner1)
            l2 = lca_of_edge(inner2)
            if l1 and l2:
                return lca_node_id(l1, l2)
        return None
    l1 = lca_of_edge(edge_id1)
    l2 = lca_of_edge(edge_id2)
    if l1 and l2:
        return lca_node_id(l1, l2)
    return None


def lca_node_id(node_id1, node_id2):
    """Least common ancestor of two node IDs (spec format T{hex}.P{p}.G{g}...)."""
    if not node_id1 or not node_id2:
        return None
    p1 = node_id1.split(".")
    p2 = node_id2.split(".")
    if p1[0] != p2[0]:
        return None
    out = []
    for a, b in zip(p1, p2):
        if a == b:
            out.append(a)
        else:
            break
    return ".".join(out) if out else None


def lca_folder_path(node_id):
    """Memory folder path for a node (LCA or single node). node_id in spec format T{hex}.P{p}.G{g}..."""
    from .memory_paths import (
        MEMORY_ROOT,
        task_node_dir,
        pair_node_dir,
        grid_node_dir,
        object_node_dir,
        pixel_node_dir,
        pixel_under_object_dir,
    )
    parts = node_id.split(".")
    if not parts or not parts[0].startswith("T"):
        raise ValueError(f"Invalid node_id: {node_id}")
    hex_code = parts[0][1:]
    if len(parts) == 1:
        return task_node_dir(hex_code)
    # P, G, O, X
    i = 1
    _p = parts[i][1:] if parts[i].startswith("P") else None
    pair_id = int(_p) if _p is not None and _p.isdigit() else _p
    if len(parts) == 2:
        return pair_node_dir(hex_code, pair_id)
    i += 1
    grid_id = int(parts[i][1:]) if parts[i].startswith("G") else None
    if len(parts) == 3:
        return grid_node_dir(hex_code, pair_id, grid_id)
    i += 1
    if parts[i].startswith("O"):
        obj_id = int(parts[i][1:])
        if len(parts) == 4:
            return object_node_dir(hex_code, pair_id, "G", grid_id, obj_id)
        i += 1
        pixel_id = int(parts[i][1:]) if parts[i].startswith("X") else None
        return pixel_under_object_dir(hex_code, pair_id, "G", grid_id, obj_id, pixel_id)
    else:
        pixel_id = int(parts[i][1:]) if parts[i].startswith("X") else None
        return pixel_node_dir(hex_code, pair_id, "G", grid_id, pixel_id)


def build_edge_id_1order(node_id1, node_id2):
    """Edge ID for 1st-order comparison (node vs node). E_{short1}-{short2}."""
    s1 = node_id_to_short_name(node_id1)
    s2 = node_id_to_short_name(node_id2)
    return f"E_{s1}-{s2}"


def edge_path_for_comparison(node_id1, node_id2, edge_id):
    """Full path for a comparison edge file: LCA folder + edge_id + .json"""
    lca = lca_node_id(node_id1, node_id2)
    if not lca:
        raise ValueError(f"No LCA for {node_id1}, {node_id2}")
    folder = lca_folder_path(lca)
    return folder + edge_id + ".json"

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
