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
from managers.arc_manager import ARCManager
from pprint import pprint
import os
import json


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
            # For 2D lists, check if each sublist has the same set of elements and same length
            all_common = True
            for i, (sublist1, sublist2) in enumerate(zip(comp1, comp2)):
                if not isinstance(sublist1, list) or not isinstance(sublist2, list):
                    all_common = False
                    break
                if set(sublist1) != set(sublist2) or len(sublist1) != len(sublist2):
                    all_common = False
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

def compare(comp1, comp2, save=True):
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

    if save:
        save_comparison_result(final_data, id_pair_to_comparison_path(id1, id2))
        # print(f"Combined comparison data saved to: {id_pair_to_comparison_path(id1, id2)}")

        return final_data

    return final_data

# def compare_from_ids(id1, id2):
#     comp1 = load_json_file(id_to_json_path(id1))
#     comp2 = load_json_file(id_to_json_path(id2))
    
#     return compare(comp1, comp2)





def id_to_json_path(id):
    # id는 이제 경로 문자열 (예: "007bbfb7.PAIR_nodes.0")
    root = "memory/"
    
    # 경로를 점으로 분리
    path_parts = id.split('.')
    
    if len(path_parts) == 1:
        # TASK level
        task_hex = path_parts[0]
        return f"{root}TASK_nodes/TASK_{task_hex}/TASK_property/TASK_{task_hex}_property.json"
    elif len(path_parts) == 3 and path_parts[1] == "PAIR_nodes":
        # PAIR level: "007bbfb7.PAIR_nodes.0"
        task_hex = path_parts[0]
        pair_num = path_parts[2]
        return f"{root}TASK_nodes/TASK_{task_hex}/PAIR_nodes/PAIR_{pair_num}/PAIR_property/PAIR_{pair_num}_property.json"
    elif len(path_parts) == 5 and path_parts[1] == "PAIR_nodes" and path_parts[3] == "GRID_nodes":
        # GRID level: "007bbfb7.PAIR_nodes.0.GRID_nodes.0"
        task_hex = path_parts[0]
        pair_num = path_parts[2]
        grid_num = path_parts[4]
        return f"{root}TASK_nodes/TASK_{task_hex}/PAIR_nodes/PAIR_{pair_num}/GRID_nodes/GRID_{grid_num}/GRID_property/GRID_{grid_num}_property.json"
    elif len(path_parts) == 7 and path_parts[1] == "PAIR_nodes" and path_parts[3] == "GRID_nodes" and path_parts[5] == "OBJECT_nodes":
        # OBJECT level: "007bbfb7.PAIR_nodes.0.GRID_nodes.0.OBJECT_nodes.0"
        task_hex = path_parts[0]
        pair_num = path_parts[2]
        grid_num = path_parts[4]
        obj_num = path_parts[6]
        return f"{root}TASK_nodes/TASK_{task_hex}/PAIR_nodes/PAIR_{pair_num}/GRID_nodes/GRID_{grid_num}/OBJECT_nodes/OBJECT_{obj_num}/OBJECT_property/OBJECT_{obj_num}_property.json"
    elif len(path_parts) == 7 and path_parts[1] == "PAIR_nodes" and path_parts[3] == "GRID_nodes" and path_parts[5] == "PIXEL_nodes":
        # PIXEL level (grid direct): "007bbfb7.PAIR_nodes.0.GRID_nodes.0.PIXEL_nodes.0"
        task_hex = path_parts[0]
        pair_num = path_parts[2]
        grid_num = path_parts[4]
        pixel_num = path_parts[6]
        return f"{root}TASK_nodes/TASK_{task_hex}/PAIR_nodes/PAIR_{pair_num}/GRID_nodes/GRID_{grid_num}/PIXEL_nodes/PIXEL_{pixel_num}/PIXEL_property/PIXEL_{pixel_num}_property.json"
    elif len(path_parts) == 9 and path_parts[1] == "PAIR_nodes" and path_parts[3] == "GRID_nodes" and path_parts[5] == "OBJECT_nodes" and path_parts[7] == "PIXEL_nodes":
        # PIXEL level (object): "007bbfb7.PAIR_nodes.0.GRID_nodes.0.OBJECT_nodes.0.PIXEL_nodes.0"
        task_hex = path_parts[0]
        pair_num = path_parts[2]
        grid_num = path_parts[4]
        obj_num = path_parts[6]
        pixel_num = path_parts[8]
        return f"{root}TASK_nodes/TASK_{task_hex}/PAIR_nodes/PAIR_{pair_num}/GRID_nodes/GRID_{grid_num}/OBJECT_nodes/OBJECT_{obj_num}/PIXEL_nodes/PIXEL_{pixel_num}/PIXEL_property/PIXEL_{pixel_num}_property.json"
    else:
        raise ValueError(f"Invalid id format: {id}")

def json_path_to_id(json_path):
    root = "memory/"
    path_parts = json_path.split(root)[-1].split("/")
    
    if "TASK_property" in json_path:
        # TASK level
        task_hex = path_parts[1].split("_")[-1]
        return task_hex
    elif "PAIR_property" in json_path:
        # PAIR level
        task_hex = path_parts[1].split("_")[-1]
        pair_num = path_parts[3].split("_")[-1]
        return f"{task_hex}.PAIR_nodes.{pair_num}"
    elif "GRID_property" in json_path:
        # GRID level
        task_hex = path_parts[1].split("_")[-1]
        pair_num = path_parts[3].split("_")[-1]
        grid_num = path_parts[5].split("_")[-1]
        return f"{task_hex}.PAIR_nodes.{pair_num}.GRID_nodes.{grid_num}"
    elif "OBJECT_property" in json_path:
        # OBJECT level
        task_hex = path_parts[1].split("_")[-1]
        pair_num = path_parts[3].split("_")[-1]
        grid_num = path_parts[5].split("_")[-1]
        obj_num = path_parts[7].split("_")[-1]
        return f"{task_hex}.PAIR_nodes.{pair_num}.GRID_nodes.{grid_num}.OBJECT_nodes.{obj_num}"
    elif "PIXEL_property" in json_path:
        # PIXEL level
        task_hex = path_parts[1].split("_")[-1]
        pair_num = path_parts[3].split("_")[-1]
        grid_num = path_parts[5].split("_")[-1]
        
        # PIXEL이 OBJECT 아래에 있는지 GRID 아래에 있는지 확인
        if "OBJECT_nodes" in json_path:
            # OBJECT 아래의 PIXEL
            obj_num = path_parts[7].split("_")[-1]
            pixel_num = path_parts[9].split("_")[-1]
            return f"{task_hex}.PAIR_nodes.{pair_num}.GRID_nodes.{grid_num}.OBJECT_nodes.{obj_num}.PIXEL_nodes.{pixel_num}"
        else:
            # GRID 아래의 PIXEL
            pixel_num = path_parts[7].split("_")[-1]
            return f"{task_hex}.PAIR_nodes.{pair_num}.GRID_nodes.{grid_num}.PIXEL_nodes.{pixel_num}"
    else:
        raise ValueError(f"Invalid json path: {json_path}")
    
def id_pair_to_comparison_path(id1, id2):
    root = "memory/"
    
    # id1과 id2는 이제 경로 문자열
    # 첫 번째 부분에서 task hex code를 추출
    task_hex1 = id1.split('.')[0]
    task_hex2 = id2.split('.')[0]
    
    # 경로를 점으로 분리하여 타입을 판단
    path_parts1 = id1.split('.')
    path_parts2 = id2.split('.')
    
    if len(path_parts1) == 1:
        # TASK level
        return f"{root}TASK_edges/TASK_{task_hex1}-TASK_{task_hex2}.json"
    elif len(path_parts1) == 3 and path_parts1[1] == "PAIR_nodes":
        # PAIR level: "007bbfb7.PAIR_nodes.0"
        pair_num1 = path_parts1[2]
        pair_num2 = path_parts2[2]
        return f"{root}TASK_nodes/TASK_{task_hex1}/PAIR_edges/PAIR/PAIR_{pair_num1}-PAIR_{pair_num2}.json"
    elif len(path_parts1) == 5 and path_parts1[1] == "PAIR_nodes" and path_parts1[3] == "GRID_nodes":
        # GRID level: "007bbfb7.PAIR_nodes.0.GRID_nodes.0"
        pair_num1 = path_parts1[2]
        pair_num2 = path_parts2[2]
        grid_num1 = path_parts1[4]
        grid_num2 = path_parts2[4]
        return f"{root}TASK_nodes/TASK_{task_hex1}/PAIR_nodes/PAIR_{pair_num1}/GRID_edges/GRID/GRID_{grid_num1}-GRID_{grid_num2}.json"
    elif len(path_parts1) == 7 and path_parts1[1] == "PAIR_nodes" and path_parts1[3] == "GRID_nodes" and path_parts1[5] == "OBJECT_nodes":
        # OBJECT level: "007bbfb7.PAIR_nodes.0.GRID_nodes.0.OBJECT_nodes.0"
        pair_num1 = path_parts1[2]
        pair_num2 = path_parts2[2]
        grid_num1 = path_parts1[4]
        grid_num2 = path_parts2[4]
        obj_num1 = path_parts1[6]
        obj_num2 = path_parts2[6]
        return f"{root}TASK_nodes/TASK_{task_hex1}/PAIR_nodes/PAIR_{pair_num1}/GRID_edges/OBJECT/OBJECT_{obj_num1}-OBJECT_{obj_num2}.json"
    elif len(path_parts1) == 7 and path_parts1[1] == "PAIR_nodes" and path_parts1[3] == "GRID_nodes" and path_parts1[5] == "PIXEL_nodes":
        # PIXEL level (grid direct): "007bbfb7.PAIR_nodes.0.GRID_nodes.0.PIXEL_nodes.0"
        pair_num1 = path_parts1[2]
        pair_num2 = path_parts2[2]
        grid_num1 = path_parts1[4]
        grid_num2 = path_parts2[4]
        pixel_num1 = path_parts1[6]
        pixel_num2 = path_parts2[6]
        return f"{root}TASK_nodes/TASK_{task_hex1}/PAIR_nodes/PAIR_{pair_num1}/GRID_edges/PIXEL/PIXEL_{pixel_num1}-PIXEL_{pixel_num2}.json"
    elif len(path_parts1) == 9 and path_parts1[1] == "PAIR_nodes" and path_parts1[3] == "GRID_nodes" and path_parts1[5] == "OBJECT_nodes" and path_parts1[7] == "PIXEL_nodes":
        # PIXEL level (object): "007bbfb7.PAIR_nodes.0.GRID_nodes.0.OBJECT_nodes.0.PIXEL_nodes.0"
        pair_num1 = path_parts1[2]
        pair_num2 = path_parts2[2]
        grid_num1 = path_parts1[4]
        grid_num2 = path_parts2[4]
        obj_num1 = path_parts1[6]
        obj_num2 = path_parts2[6]
        pixel_num1 = path_parts1[8]
        pixel_num2 = path_parts2[8]
        return f"{root}TASK_nodes/TASK_{task_hex1}/PAIR_nodes/PAIR_{pair_num1}/GRID_nodes/GRID_{grid_num1}/OBJECT_nodes/OBJECT_{obj_num1}/PIXEL_edges/PIXEL/PIXEL_{pixel_num1}-PIXEL_{pixel_num2}.json"
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
    elif component.type == "grid" or component.type == "tfgrid":
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
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    # print(f"Comparison result saved to: {output_path}") # Uncomment to print the output path

            


if __name__ == "__main__":
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
