import json
from collections import deque
from pprint import pprint

# def bfs_traverse_comparison_tree(comparison_result):
#     if "result" in comparison_result:
#         comparison_result = comparison_result["result"]
    
#     visited_nodes = []
#     queue = deque([("result", comparison_result, [])])
    
#     while queue:
#         node_name, node_data, path = queue.popleft()
#         current_path = path + [node_name]
        
#         # Record the current node
#         visited_nodes.append({
#             "name": node_name,
#             "path": current_path,
#             "type": node_data.get("type", "unknown"),
#             "score": node_data.get("score", "unknown"),
#             "category": node_data.get("category", {}),
#             "data": node_data
#         })
        
#         # If this node has subcategories, add them to the queue
#         if "category" in node_data and node_data["category"]:
#             for sub_name, sub_data in node_data["category"].items():
#                 queue.append((sub_name, sub_data, current_path))
    
#     return visited_nodes

# def dfs_traverse_comparison_tree(comparison_result):
#     if "result" in comparison_result:
#         comparison_result = comparison_result["result"]
    
#     visited_nodes = []
    
#     def dfs_recursive(node_name, node_data, path):
#         current_path = path + [node_name]
        
#         # Visit current node first (preorder)
#         visited_nodes.append({
#             "name": node_name,
#             "path": current_path,
#             "type": node_data.get("type", "unknown"),
#             "score": node_data.get("score", "unknown"),
#             "category": node_data.get("category", {}),
#             "data": node_data
#         })
        
#         # Visit children recursively
#         if "category" in node_data and node_data["category"]:
#             for sub_name, sub_data in node_data["category"].items():
#                 dfs_recursive(sub_name, sub_data, current_path)
    
#     dfs_recursive("result", comparison_result, [])
#     return visited_nodes

# Generate rules for DIFF type - focusing on what needs to change
def rule_generator_diff(comparison_result):
    rules = []
    rule_template = {
        "condition": {
            "name": "name", # category
            "type": "type" # DIFF/COMM
        },
        "action": {
            "name": "", # DSL name
            "args": {} # DSL parameters
        }
    }
    comparison_type = comparison_result["id1"].split(", '")[-1].split("')")[0]  # will be the same with comparison_result["id2"]
    comp1_id = comparison_result["id1"].split(", ")
    comp2_id = comparison_result["id2"].split(", ")

    data = comparison_result["result"]["category"]

    # grid comparison result -> rule
    if comparison_type == "grid":
        # if size is DIFF -> make_grid with the comp2 size
        if data["size"]["type"] == "DIFF":
            rule = rule_template.copy()
            rule["condition"]["name"] = "size"
            rule["condition"]["type"] = "DIFF"
            rule["action"]["name"] = "make_grid"
            rule["action"]["args"] = {
                "1": data["size"]["category"]["height"]["comp2"],
                "2": data["size"]["category"]["width"]["comp2"], 
                "3": 13
            }
            rules.append(rule)

        # if color is DIFF -> append comp1 and comp2 color to add_color/remove_color variable(list)
        # if color is DIFF -> assert output_grid color satisfies comp2 color
        if data["color"]["type"] == "DIFF":
            for key, value in data["color"]["category"].items():
                rule = rule_template.copy()
                rule["condition"]["name"] = "color"
                rule["condition"]["type"] = "DIFF"
                rule["action"]["name"] = "add_color"
                rule["action"]["args"] = {
                    "1": key
                }
                rules.append(rule)
            
            for key, value in data["color"]["category"].items():
                rule = rule_template.copy()
                rule["condition"]["name"] = "color"
                rule["condition"]["type"] = "DIFF"
                rule["action"]["name"] = "remove_color"
                rule["action"]["args"] = {
                    "1": key
                }
                rules.append(rule)

        # if area is DIFF -> assert output_grid area satisfies comp2 area # TODO: 아직 어떤 규칙이 필요한지 모르겠음
        if data["area"]["type"] == "DIFF":
            rule = rule_template.copy()
            rules.append(rule)
        
        # if symmetry is DIFF -> assert output_grid symmetry satisfies comp2 symmetry # TODO: 아직 어떤 규칙이 필요한지 모르겠음
        if data["symmetry"]["type"] == "DIFF":
            rule = rule_template.copy()
            rules.append(rule)

    breakpoint()
    return rules


if __name__ == "__main__":
    from managers.arc_manager import ARCManager
    from comparison import compare

    TASK_HEX_CODE = "007bbfb7"
    # TASK_HEX_CODE = "08ed6ac7"
    task = ARCManager.from_hex_code(TASK_HEX_CODE)

    pnum = (0, 0)
    gnum = (0, 1)
    onum = (1, 2)
    xnum = (2, 0)
    typ = "grid"
    
    input_grid = task.example_pairs[pnum[0]].input_grid
    output_grid = task.example_pairs[pnum[1]].output_grid

    object1 = input_grid.objects[onum[0]]
    object2 = output_grid.objects[onum[1]]

    pixel1 = input_grid.pixels[xnum[0]]
    pixel2 = output_grid.pixels[xnum[1]]

    if typ == "grid":
        comp1 = input_grid
        comp2 = output_grid
    elif typ == "object":
        comp1 = object1
        comp2 = object2
    elif typ == "pixel":
        comp1 = pixel1
        comp2 = pixel2
    else:
        raise ValueError(f"Invalid type: {typ}")
 
    comparison_result = compare(comp1, comp2, save=False)

    print("=== Processed Comparison Result ===")
    pprint(comparison_result)
    
    with open(f"comparison_result_{TASK_HEX_CODE}_{typ}.json", "w") as f:
        json.dump(comparison_result, f, indent=2, default=str)
    
    rules = rule_generator_diff(comparison_result)
    pprint(rules)
    print(len(rules))
    
    