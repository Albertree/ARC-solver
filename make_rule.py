import json
from collections import deque
from pprint import pprint

def bfs_traverse_comparison_tree(comparison_result):
    if "result" in comparison_result:
        comparison_result = comparison_result["result"]
    
    visited_nodes = []
    queue = deque([("result", comparison_result, [])])
    
    while queue:
        node_name, node_data, path = queue.popleft()
        current_path = path + [node_name]
        
        # Record the current node
        visited_nodes.append({
            "name": node_name,
            "path": current_path,
            "type": node_data.get("type", "unknown"),
            "score": node_data.get("score", "unknown"),
            "category": node_data.get("category", {}),
            "data": node_data
        })
        
        # If this node has subcategories, add them to the queue
        if "category" in node_data and node_data["category"]:
            for sub_name, sub_data in node_data["category"].items():
                queue.append((sub_name, sub_data, current_path))
    
    return visited_nodes

def dfs_traverse_comparison_tree(comparison_result):
    if "result" in comparison_result:
        comparison_result = comparison_result["result"]
    
    visited_nodes = []
    
    def dfs_recursive(node_name, node_data, path):
        current_path = path + [node_name]
        
        # Visit current node first (preorder)
        visited_nodes.append({
            "name": node_name,
            "path": current_path,
            "type": node_data.get("type", "unknown"),
            "score": node_data.get("score", "unknown"),
            "category": node_data.get("category", {}),
            "data": node_data
        })
        
        # Visit children recursively
        if "category" in node_data and node_data["category"]:
            for sub_name, sub_data in node_data["category"].items():
                dfs_recursive(sub_name, sub_data, current_path)
    
    dfs_recursive("result", comparison_result, [])
    return visited_nodes


# def analyze_tree_structure(comparison_result):
#     bfs_nodes = bfs_traverse_comparison_tree(comparison_result)
#     dfs_nodes = dfs_traverse_comparison_tree(comparison_result)
    
    
#     # Count by type
#     diff_nodes = [node for node in bfs_nodes if node["type"] == "DIFF"]
#     comm_nodes = [node for node in bfs_nodes if node["type"] == "COMM"]
    
#     analysis = {
#         "total_nodes": len(bfs_nodes),
#         "diff_nodes": len(diff_nodes),
#         "comm_nodes": len(comm_nodes),
#         "max_depth": max(len(node["path"]) for node in bfs_nodes) if bfs_nodes else 0,
#         "bfs_order": [node["name"] for node in bfs_nodes],
#         "dfs_order": [node["name"] for node in dfs_nodes]
#     }
    
#     return analysis



# def rule_generator(comparison_result, type="DIFF"):
#     data = comparison_result["result"]["category"]
#     rule_chunk = []
#     for key, value in data.items():
#         print(f"Processing category: {key}")
#         if value["type"] == "DIFF":
#             rules = rule_generator_diff(value, key)
#             rule_chunk.extend(rules)
#         elif value["type"] == "COMM":
#             rules = rule_generator_comm(value, key)
#             rule_chunk.extend(rules)
#         else:
#             raise ValueError("Invalid type. Check the type.")
#         print()
#     print("--------------------------------")
#     print("Generated rules:")
#     for rule in rule_chunk:
#         print(rule)
#     return rule_chunk

# Generate rules for DIFF type - focusing on what needs to change
def rule_generator_diff(comparison_result, traversal_method="BFS"):
    if "result" in comparison_result:
        print("in if")
        comparison_result = comparison_result["result"]

    data = comparison_result["category"]
    
    if data["size"]["type"] == "DIFF":
        rule = {
            "condition": {"name": "size",
                          "type": "DIFF"
                          },
            "action": {"name": "make_grid",
                       "args": [data["size"]["category"]["height"]["comp2"], data["size"]["category"]["width"]["comp2"], 13]
                       }
        }

        print(rule)
        breakpoint()
        return rule
    # print(f"DIFF rule generator using {traversal_method} traversal")
    # rules = []
    
    # # Select traversal method
    # if traversal_method.upper() == "BFS":
    #     traversed_nodes = bfs_traverse_comparison_tree(comparison_result)
    # elif traversal_method.upper() == "DFS":
    #     traversed_nodes = dfs_traverse_comparison_tree(comparison_result)
    # else:
    #     raise ValueError("traversal_method must be 'BFS' or 'DFS'")
    
    # # Find DIFF nodes that are leaf nodes (empty category)
    # diff_leaf_nodes = [
    #     node for node in traversed_nodes 
    #     if node["type"] == "DIFF" and 
    #     node["category"] == {}
    # ]

    rule = {
        "condition": {},
        "action": {}
    }

    added_color = []
    removed_color = []

    print(f"Found {len(diff_leaf_nodes)} DIFF leaf nodes")
    pprint(diff_leaf_nodes)
    breakpoint()

    for node in diff_leaf_nodes:
        current_data = node["data"]
        comp2_value = current_data["data"]["comp2"]

        if "size" in node["path"]:
           rule["condition"] = {"name": "size",
                                "type": "DIFF"
                                }

           rule["action"] = {"name": "make_grid",
                             "args": [comp2_value]
                            }
    
    return rules

def rule_generator_comm(category_result, category_name):
    print("COMM rule generator")
    rules = []
    
    # Use DFS traversal to find COMM nodes
    dfs_nodes = dfs_traverse_comparison_tree({"result": category_result})
    comm_nodes = [node for node in dfs_nodes if node["type"] == "COMM"]
    
    print(f"Found {len(comm_nodes)} COMM nodes in DFS traversal:")
    for node in comm_nodes:
        print(f"  - {node['name']} (Path: {' -> '.join(node['path'])})")
        
        # Generate rule for this COMM node
        if "category" in node["data"] and not node["data"]["category"]:
            # This is a leaf node with comp1/comp2 values
            comp2_value = node["data"].get("comp2")
            rule = {
                "conditions": {},
                "actions": {}
            }
            
            if isinstance(comp2_value, (int, float)) and comp2_value > 0:
                rule["actions"][f"{node['name']}"] = "keep"
            elif isinstance(comp2_value, bool) and comp2_value:
                rule["actions"][f"{node['name']}"] = "keep"
            
            if rule["actions"]:
                rules.append(rule)
    
    return rules

if __name__ == "__main__":
    from managers.arc_manager import ARCManager
    from comparison import compare, compare_from_ids

    TASK_HEX_CODE = "007bbfb7"

    task = ARCManager.from_hex_code(TASK_HEX_CODE)


    ARCManager.from_hex_code(TASK_HEX_CODE)

    pnum = (0, 0)
    gnum = (0, 1)
    onum = (1, 2)
    xnum = (9, 0)
    typ = "grid"
    
    id1 = (TASK_HEX_CODE, pnum[0], gnum[0], onum[0], xnum[0], typ)
    id2 = (TASK_HEX_CODE, pnum[1], gnum[1], onum[1], xnum[1], typ)
    comparison_result = compare_from_ids(id1, id2)

    # input_grid = task.example_pairs[0].input_grid
    # output_grid = task.example_pairs[0].output_grid

    # comparison_result = compare(input_grid.property, output_grid.property)

    
    nodes = bfs_traverse_comparison_tree(comparison_result)
    print(len(nodes))

    # Tree Structure Analysis
    # analysis = analyze_tree_structure(comparison_result)
    
    # print("\n=== Generating Rules from Comparison Result ===")
    # print("\n--- Testing BFS Traversal ---")
    # rules_bfs = rule_generator(comparison_result)
    
    # print("\n--- Testing DFS Traversal ---")
    # # Create a modified rule generator that uses DFS
    # def rule_generator_dfs(comparison_result, type="DIFF"):
    #     data = comparison_result["result"]["category"]
    #     rule_chunk = []
    #     for key, value in data.items():
    #         print(f"Processing category: {key}")
    #         if value["type"] == "DIFF":
    #             rules = rule_generator_diff(value, key, "DFS")
    #             rule_chunk.extend(rules)
    #         elif value["type"] == "COMM":
    #             pass
    #             # rules = rule_generator_comm(value, key)
    #             # rule_chunk.extend(rules)
    #         else:
    #             raise ValueError("Invalid type. Check the type.")
    #         print()
    #     print("--------------------------------")
    #     print("Generated rules:")
    #     for rule in rule_chunk:
    #         print(rule)
    #     return rule_chunk

    rules_bfs = rule_generator_diff(comparison_result, "BFS")
    pprint(rules_bfs)
    print(len(rules_bfs))
    # rules_dfs = rule_generator_dfs(comparison_result)
    
    