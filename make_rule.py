import json
import os
from collections import deque
from pprint import pprint

def extract_comparison_level(id):
    """Extract comparison level from id string with priority order: PIXEL > OBJECT > GRID > PAIR > TASK"""
    if "PIXEL" in id:
        return "PIXEL"
    elif "OBJECT" in id:
        return "OBJECT"
    elif "GRID" in id:
        return "GRID"
    elif "PAIR" in id:
        return "PAIR"
    elif "TASK" in id:
        return "TASK"
    else:
        return "UNKNOWN"

def load_matching_rules(comparison_level, category_key):
    """Load rule basket JSON files that match the comparison level and category"""
    rule_basket_dir = "rule_basket"
    rules = []
    
    if not os.path.exists(rule_basket_dir):
        return rules
    
    for filename in os.listdir(rule_basket_dir):
        if filename.endswith('.json'):
            # Extract the part before first underscore (comparison level) and second part (category)
            parts = filename.split('_')
            if len(parts) >= 2:
                file_level = parts[0]
                file_category = parts[1]
                
                # Check if both comparison level and category match
                if file_level == comparison_level and file_category == category_key:
                    filepath = os.path.join(rule_basket_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            rule_data = json.load(f)
                            if 'rules' in rule_data:
                                rules.extend(rule_data['rules'])
                    except Exception as e:
                        print(f"Error loading {filepath}: {e}")
    
    return rules

def evaluate_rule_condition(condition, comparison_result):
    """Evaluate a rule condition against comparison result"""
    if isinstance(condition, dict):
        if 'operator' in condition:
            if condition['operator'] == '==':
                operand1 = get_nested_value(comparison_result, condition['operand1'])
                operand2 = condition['operand2']
                return operand1 == operand2
            elif condition['operator'] == 'AND':
                return (evaluate_rule_condition(condition['operand1'], comparison_result) and 
                       evaluate_rule_condition(condition['operand2'], comparison_result))
            elif condition['operator'] == 'OR':
                return (evaluate_rule_condition(condition['operand1'], comparison_result) or 
                       evaluate_rule_condition(condition['operand2'], comparison_result))
    return False

def get_nested_value(data, path):
    """Get nested value from data using dot notation path"""
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and key.isdigit():
            current = current[int(key)]
        else:
            return None
    
    return current

def get_matching_actions(comparison_result):
    """Get matching actions from rule basket based on comparison result"""
    actions = []
    
    # Get comparison level from id
    comparison_level = extract_comparison_level(comparison_result["id1"])
    
    # Check if result and category exist
    if "result" not in comparison_result or "category" not in comparison_result["result"]:
        return actions
    
    # Loop through each category in comparison result
    for category_key in comparison_result["result"]["category"].keys():
        # Load matching rules for this comparison level and category
        rules = load_matching_rules(comparison_level, category_key)
        
        # Check each rule
        for rule in rules:
            if 'condition' in rule and 'action' in rule:
                # Evaluate the condition
                if evaluate_rule_condition(rule['condition'], comparison_result):
                    # Condition matches, add the action
                    action = rule['action'].copy()
                    
                    # Process action arguments to replace placeholders with actual values
                    if 'args' in action:
                        processed_args = {}
                        for key, value in action['args'].items():
                            if isinstance(value, str) and value.startswith('result.'):
                                # Replace placeholder with actual value
                                actual_value = get_nested_value(comparison_result, value)
                                if actual_value is not None:
                                    processed_args[key] = actual_value
                                else:
                                    processed_args[key] = value
                            else:
                                processed_args[key] = value
                        action['args'] = processed_args
                    
                    actions.append(action)
    
    return actions

# Legacy function name for backward compatibility
def rule_generator_diff(comparison_result):
    """Legacy function name - use get_matching_actions instead"""
    return get_matching_actions(comparison_result)

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

    # print("=== Processed Comparison Result ===")
    # pprint(comparison_result)
    
    with open(f"comparison_result_{TASK_HEX_CODE}_{typ}.json", "w") as f:
        json.dump(comparison_result, f, indent=2, default=str)
    
    actions = get_matching_actions(comparison_result)
    pprint(actions)
    print(len(actions))

    
    
    