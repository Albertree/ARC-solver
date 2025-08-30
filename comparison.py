from managers.arc_manager import ARCManager
from pprint import pprint
import os
import json

def id_to_json_path(id):
    TASK_HEX_CODE = id[0]
    pnum = id[1]
    gnum = id[2]
    onum = id[3]
    xnum = id[4]
    typ = id[5]

    if typ == "task" or typ == "t":
        return f"memory/TASK_nodes/TASK_{TASK_HEX_CODE}/TASK_property/TASK_{TASK_HEX_CODE}_property.json"
    elif typ == "pair" or typ == "p":
        return f"memory/TASK_nodes/TASK_{TASK_HEX_CODE}/PAIR_nodes/PAIR_{pnum}/PAIR_property/PAIR_{pnum}_property.json"
    elif typ == "grid" or typ == "g":
        return f"memory/TASK_nodes/TASK_{TASK_HEX_CODE}/PAIR_nodes/PAIR_{pnum}/GRID_nodes/GRID_{gnum}/GRID_property/GRID_{gnum}_property.json"
    elif typ == "object" or typ == "o":
        return f"memory/TASK_nodes/TASK_{TASK_HEX_CODE}/PAIR_nodes/PAIR_{pnum}/GRID_nodes/GRID_{gnum}/OBJECT_nodes/OBJECT_{onum}/OBJECT_property/OBJECT_{onum}_property.json"
    elif typ == "pixel" or typ == "x":
        return f"memory/TASK_nodes/TASK_{TASK_HEX_CODE}/PAIR_nodes/PAIR_{pnum}/GRID_nodes/GRID_{gnum}/PIXEL_nodes/PIXEL_{xnum}/PIXEL_property/PIXEL_{xnum}_property.json"
    else:
        raise ValueError("Invalid type. Check the type.")

def json_path_to_id(json_path):
    root = "memory/"
    if "TASK_property" in json_path:
        return (json_path.split(root)[-1].split("/")[1].split("_")[-1], None, None, None, None, "task")
    elif "PAIR_property" in json_path:
        return (json_path.split(root)[-1].split("/")[1].split("_")[-1], json_path.split(root)[-1].split("/")[-3].split("_")[-1], None, None, None, "pair")
    elif "GRID_property" in json_path:
        return (json_path.split(root)[-1].split("/")[1].split("_")[-1], json_path.split(root)[-1].split("/")[-5].split("_")[-1], json_path.split(root)[-1].split("/")[-3].split("_")[-1], None, None, "grid")
    elif "OBJECT_property" in json_path:
        return (json_path.split(root)[-1].split("/")[1].split("_")[-1], json_path.split(root)[-1].split("/")[-7].split("_")[-1], json_path.split(root)[-1].split("/")[-5].split("_")[-1], json_path.split(root)[-1].split("/")[-3].split("_")[-1], None, "object")
    elif "PIXEL_property" in json_path:
        return (json_path.split(root)[-1].split("/")[1].split("_")[-1], json_path.split(root)[-1].split("/")[-7].split("_")[-1], json_path.split(root)[-1].split("/")[-5].split("_")[-1], None, json_path.split(root)[-1].split("/")[-3].split("_")[-1], "pixel")
    else:
        raise ValueError("Invalid json path. Check the json path.")

def load_json_file(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"File not found: {json_path}")
    with open(json_path, "r") as f:
        return json.load(f)

def compare(comp1, comp2, path=""):
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
        if len(comp1) != len(comp2):
            result["type"] = "DIFF"
            return result
        
        # Compare each element in the list
        list_results = []
        all_common = True
        for i, (item1, item2) in enumerate(zip(comp1, comp2)):
            item_result = compare(item1, item2, f"{path}[{i}]")
            list_results.append(item_result)
            if item_result["type"] == "DIFF":
                all_common = False
        
        result["type"] = "COMM" if all_common else "DIFF"
        result["details"] = list_results
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
                key_result = compare(comp1[key], comp2[key], key_path)
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

def get_combined_comparison_data(comparison_result):
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
                for sub_key, sub_value in sub_details.items():
                    result["category"][sub_key] = process_category_recursive(sub_value)
        else:
            # Add comp1 and comp2 only if this is a leaf node (no subcategories)
            if isinstance(category_data, dict) and "comp1" in category_data and "comp2" in category_data:
                result["comp1"] = category_data["comp1"]
                result["comp2"] = category_data["comp2"]
        
        return result
    
    # Process top-level categories
    combined_data = {
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
            
            combined_data["score"] = f"{comm_categories}/{total_categories}"
            
            # Process each category
            sorted_items = sorted(details.items())
            for category_name, category_data in sorted_items:
                combined_data["category"][category_name] = process_category_recursive(category_data)
    
    return combined_data

def save_comparison_result(comparison_result, output_path, comp1_repr="", comp2_repr=""):
    combined_data = get_combined_comparison_data(comparison_result)
    
    # Create the final structure with comp1, comp2, and result
    final_data = {
        "comp1": comp1_repr,
        "comp2": comp2_repr,
        "result": combined_data
    }
    
    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=2, default=str)
    
    print(f"Combined comparison data saved to: {output_path}")

def print_comparison_result(comparison_result):
    print("=== Comparison Result and Scores ===")
    # Count top-level categories
    if isinstance(comparison_result, dict) and "details" in comparison_result:
        details = comparison_result["details"]
        if isinstance(details, dict):
            comm_categories = 0
            total_categories = len(details)
            for category_name, category_data in details.items():
                if isinstance(category_data, dict) and category_data.get("type") == "COMM":
                    comm_categories += 1
            
            # Determine status and type
            if comm_categories == total_categories:
                status = "✓"
                category_type = "COMM"
            else:
                status = "✗"
                category_type = "DIFF"
            
            print(f"{status}: {comm_categories}/{total_categories} {category_type}")
    
    
    
    def print_category_scores_recursive(result_dict, indent=0):
        """Recursively print category scores with indentation."""
        if not isinstance(result_dict, dict) or "details" not in result_dict:
            return
        
        details = result_dict["details"]
        if not isinstance(details, dict):
            return
        
        prefix = " " * 30 * indent  # 30 spaces per indentation level
        
        # Sort category names for consistent output
        sorted_items = sorted(details.items())
        for category_name, category_data in sorted_items:
            # Check if this category has deeper subcategories
            has_deeper_subcategories = False
            if isinstance(category_data, dict) and "details" in category_data:
                sub_details = category_data["details"]
                if isinstance(sub_details, dict):
                    has_deeper_subcategories = any(
                        isinstance(sub_value, dict) and "details" in sub_value and sub_value["details"]
                        for sub_value in sub_details.values()
                    )
            
            # Count COMM and DIFF in this category
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
            
            if total_count > 0:
                status = "✓" if category_data.get("type") == "COMM" else "✗"
                print(f"{prefix}{status} {category_name}: {comm_count}/{total_count} ({category_data.get('type', 'MIXED')})")
            else:
                # No subcategories to count
                status = "✓" if category_data.get("type") == "COMM" else "✗"
                print(f"{prefix}{status} {category_name}: ({category_data.get('type', 'MIXED')})")
            
            # Always print subcategories if they exist
            if isinstance(category_data, dict) and "details" in category_data:
                sub_details = category_data["details"]
                if isinstance(sub_details, dict):
                    print_category_scores_recursive(category_data, indent + 1)
    
    # Start with 30 spaces indentation for all category scores
    print_category_scores_recursive(comparison_result, indent=1)
    print("=" * 30)

            
if __name__ == "__main__":
    # comparing from memory (.json)

    TASK_HEX_CODE = "08ed6ac7"
    ARCManager.from_hex_code(TASK_HEX_CODE)

    pnum = (0, 0)
    gnum = (0, 1)
    onum = (1, 2)
    xnum = (9, 0)
    typ = "pixel"
    
    id1 = (TASK_HEX_CODE, pnum[0], gnum[0], onum[0], xnum[0], typ)
    id2 = (TASK_HEX_CODE, pnum[1], gnum[1], onum[1], xnum[1], typ)
    
    comp1 = load_json_file(id_to_json_path(id1))
    comp2 = load_json_file(id_to_json_path(id2))
    
    result = compare(comp1, comp2)
    
    # # Print the comparison score
    # print_comparison_result(result)
    
    # Save to JSON file
    output_path = f"comparison_result_{TASK_HEX_CODE}_{typ}.json"
    save_comparison_result(result, output_path, f"ID: {id1}", f"ID: {id2}")
