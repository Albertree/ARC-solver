import json
from collections import deque
from pprint import pprint

def bfs_traverse_comparison_tree(comparison_result):
    # if not comparison_result or "result" not in comparison_result:
    #     return []
    
    visited_nodes = []
    queue = deque([("result", comparison_result["result"], [])])
    
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
    # if not comparison_result or "result" not in comparison_result:
    #     return []
    
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
    
    dfs_recursive("result", comparison_result["result"], [])
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
    print(f"DIFF rule generator using {traversal_method} traversal")
    rules = []
    
    # Select traversal method
    if traversal_method.upper() == "BFS":
        traversed_nodes = bfs_traverse_comparison_tree(comparison_result)
    elif traversal_method.upper() == "DFS":
        traversed_nodes = dfs_traverse_comparison_tree(comparison_result)
    else:
        raise ValueError("traversal_method must be 'BFS' or 'DFS'")
    
    # Find DIFF nodes that are leaf nodes (empty category)
    diff_leaf_nodes = [
        node for node in traversed_nodes 
        if node["type"] == "DIFF" and 
        node["category"] == {}
    ]

    rule = {
        "condition": {},
        "action": {}
    }

    added_color = []
    removed_color = []

    for node in diff_leaf_nodes:
        current_data = node["data"]
        comp2_value = current_data.get("data").get("comp2")
        # comp1_value = current_data.get("data").get("comp1")
        
        if "color" in node["path"]:
            if comp2_value == True: 
                added_color.append(comp2_value)
            else:# comp2_value == False:
                removed_color.append(comp2_value)

        if "area" in node["path"]:
            if comp2_value == True: 
                added_color.append(comp2_value)
            else:# comp2_value == False:
                removed_color.append(comp2_value)

        if "size" in node["path"]:
            if comp2_value == True: 
                added_color.append(comp2_value)
            else:# comp2_value == False:
                removed_color.append(comp2_value)
    
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
    with open("comparison_result_08ed6ac7_grid.json", "r") as f:
        comparison_result = json.load(f)
    
    nodes = bfs_traverse_comparison_tree(comparison_result)
    pprint(nodes)
    print(len(nodes))
    breakpoint()

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
    
    