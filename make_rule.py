import json
import os
from collections import deque
from pprint import pprint

def extract_comparison_level(id):
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
    rule_basket_dir = "DSL_precondition"
    rules = []
    
    if not os.path.exists(rule_basket_dir):
        return rules
    
    for filename in os.listdir(rule_basket_dir):
        if filename.endswith('.json'):
            # Extract the part before first underscore (comparison level) and second part (category)
            parts = filename.split('.json')[0].split('_')

            if len(parts) >= 2:
                file_level = parts[0]
                file_category = parts[1]
                
                # Check if both comparison level and category match
                if file_level == comparison_level and file_category == category_key:
                    filepath = os.path.join(rule_basket_dir, filename)
             
                    try:
                        with open(filepath, 'r') as f:
                            rule_data = json.load(f)
                            rules.append(rule_data)
                    except Exception as e:
                        print(f"Error loading {filepath}: {e}")

    return rules

def evaluate_rule_condition(condition, comparison_result, parameters=None):
    if isinstance(condition, dict):
        if 'operator' in condition:
            if condition['operator'] in ['==', '!=']:
                operand1_path = condition['operand1']
                operand2 = condition['operand2']
                
                # Substitute parameters in operand1 path if parameters are provided
                if parameters:
                    operand1_path = substitute_parameters(operand1_path, parameters)
                
                operand1 = get_nested_value(comparison_result, operand1_path)
                
                # Convert operand2 to match operand1's type for comparison
                if isinstance(operand1, bool):
                    if operand2 == "True":
                        operand2 = True
                    elif operand2 == "False":
                        operand2 = False
                    elif operand2 is False:
                        operand2 = False
                    elif operand2 is True:
                        operand2 = True
                elif isinstance(operand1, (int, float)):
                    try:
                        operand2 = type(operand1)(operand2)
                    except (ValueError, TypeError):
                        pass  # Keep operand2 as string if conversion fails
                
                if condition['operator'] == '==':
                    result = operand1 == operand2
                else:  # !=
                    result = operand1 != operand2
                # print(f"  Evaluating: {operand1_path} {condition['operator']} {operand2}")
                # print(f"  operand1: {operand1} (type: {type(operand1)}), operand2: {operand2} (type: {type(operand2)}), result: {result}")
                return result
            elif condition['operator'] == 'AND':
                left_result = evaluate_rule_condition(condition['operand1'], comparison_result, parameters)
                right_result = evaluate_rule_condition(condition['operand2'], comparison_result, parameters)
                result = left_result and right_result
                # print(f"  AND: {left_result} AND {right_result} = {result}")
                return result
            elif condition['operator'] == 'OR':
                left_result = evaluate_rule_condition(condition['operand1'], comparison_result, parameters)
                right_result = evaluate_rule_condition(condition['operand2'], comparison_result, parameters)
                result = left_result or right_result
                # print(f"  OR: {left_result} OR {right_result} = {result}")
                return result
    return False

def substitute_parameters(text, parameters):
    """Substitute parameter placeholders in text with actual values"""
    if not isinstance(text, str) or not parameters:
        return text
    
    result = text
    for param_name, param_value in parameters.items():
        placeholder = f"{{{param_name}}}"
        result = result.replace(placeholder, str(param_value))
    
    return result

def get_nested_value(data, path):
    """Get nested value from data using dot notation path"""
    keys = path.split('.')
    current = data
    
    for i, key in enumerate(keys):
        if isinstance(current, dict):
            # Try exact key match first
            if key in current:
                current = current[key]
            # If key is numeric string, try converting to int
            elif key.isdigit() and int(key) in current:
                current = current[int(key)]
            else:
                return None
        elif isinstance(current, list) and key.isdigit():
            current = current[int(key)]
        else:
            return None
    
    return current

def get_usable_value_from_comparison_result(data, path):
    """Get a usable value from comparison result, handling dict structures properly"""
    value = get_nested_value(data, path)
    
    if value is None:
        return None
    
    # If the value is a dict (comparison result structure), extract the actual data
    if isinstance(value, dict):
        # Priority order: comp2 (output), comp1 (input), then the dict itself
        if 'comp2' in value:
            return value['comp2']
        elif 'comp1' in value:
            return value['comp1']
        else:
            # If no comp1/comp2, return the dict as is
            return value
    
    return value

def find_color_with_true_comp2(data, color_category_path):
    """Find the color number where comp2 is True in the color category"""
    color_category = get_nested_value(data, color_category_path)
    
    if not isinstance(color_category, dict):
        return None
    
    # Look through all color numbers (0-9) to find one where comp2 is True
    for color_num in range(10):
        color_key = str(color_num)
        if color_key in color_category:
            color_data = color_category[color_key]
            if isinstance(color_data, dict) and color_data.get('comp2') is True:
                return color_num
    
    return None

def get_parameters(parameters):
    if isinstance(parameters, list):
        return parameters
    else:
        return [parameters]

def generate_parameter_combinations(parameters, comparison_result=None):
    """Generate all possible combinations of parameter values, optionally filtered by conditions"""
    if not parameters:
        return [{}]
    
    # Get all parameter names and their possible values
    param_names = list(parameters.keys())
    param_values = []
    
    for param_name in param_names:
        param_config = parameters[param_name]
        if param_config.get('type') == 'integer' and 'range' in param_config:
            # Generate range of integers
            start, end = param_config['range']
            param_values.append(list(range(start, end + 1)))
        elif param_config.get('type') == 'string' and 'values' in param_config:
            # Use predefined string values
            param_values.append(param_config['values'])
        else:
            # Default: single value or empty list
            param_values.append([param_config.get('default', None)])
    
    # Generate all combinations
    import itertools
    combinations = []
    for combo in itertools.product(*param_values):
        combination = {}
        for i, param_name in enumerate(param_names):
            combination[param_name] = combo[i]
        
        # If comparison_result is provided, check parameter conditions
        if comparison_result is not None:
            should_include = True
            for param_name in param_names:
                param_config = parameters[param_name]
                if 'condition' in param_config:
                    # Evaluate the condition for this parameter
                    condition_result = evaluate_rule_condition(param_config['condition'], comparison_result, combination)
                    if not condition_result:
                        should_include = False
                        break
            
            if should_include:
                combinations.append(combination)
        else:
            combinations.append(combination)
    
    return combinations

def process_action_args(action_args, param_combo, comparison_result):
    processed_args = {}
    
    for key, value in action_args.items():
        if isinstance(value, str):
            substituted_value = substitute_parameters(value, param_combo)
            
            if substituted_value.startswith('result.'):
                actual_value = get_usable_value_from_comparison_result(comparison_result, substituted_value)
                if actual_value is not None:
                    # Special handling for PIXEL level coordinate
                    if key == 'selection' and isinstance(actual_value, dict) and 'category' in actual_value and 'col_index' in actual_value['category'] and 'row_index' in actual_value['category']:
                        # Extract col_index and row_index from PIXEL coordinate structure
                        col_index = actual_value['category']['col_index']
                        row_index = actual_value['category']['row_index']
                        
                        # Get the actual coordinate values
                        if isinstance(col_index, dict) and 'comp1' in col_index:
                            col_val = col_index['comp1']
                        elif isinstance(col_index, dict) and 'comp2' in col_index:
                            col_val = col_index['comp2']
                        else:
                            col_val = col_index
                            
                        if isinstance(row_index, dict) and 'comp1' in row_index:
                            row_val = row_index['comp1']
                        elif isinstance(row_index, dict) and 'comp2' in row_index:
                            row_val = row_index['comp2']
                        else:
                            row_val = row_index
                        
                        # Create coordinate tuple in list format (row, col)
                        processed_args[key] = [(row_val, col_val)]
                        print(f"DEBUG PIXEL: Generated coordinate ({row_val}, {col_val}) from col_index={col_index}, row_index={row_index}")
                    else:
                        processed_args[key] = actual_value
                else:
                    return None
            else:
                # Special handling for color parameter (only for OBJECT level)
                if key == 'color' and substituted_value.isdigit():
                    # Check if this is OBJECT level comparison (has method category)
                    if 'method' in comparison_result.get('result', {}).get('category', {}):
                        # If this is a color parameter, try to find the actual color that has comp2=True
                        color_category_path = "result.category.color.category"
                        true_color = find_color_with_true_comp2(comparison_result, color_category_path)
                        if true_color is not None:
                            processed_args[key] = true_color
                        else:
                            # Fallback to the parameter value
                            processed_args[key] = int(substituted_value)
                    else:
                        # For GRID level, use the parameter value directly
                        processed_args[key] = int(substituted_value)
                else:
                    processed_args[key] = substituted_value
        elif isinstance(value, list):
            # Handle list of paths (e.g., for selection coordinates)
            processed_list = []
            for item in value:
                if isinstance(item, str):
                    substituted_item = substitute_parameters(item, param_combo)
                    if substituted_item.startswith('result.'):
                        actual_value = get_usable_value_from_comparison_result(comparison_result, substituted_item)
                        if actual_value is not None:
                            processed_list.append(actual_value)
                        else:
                            # If any path in the list fails, skip this action
                            return None
                    else:
                        processed_list.append(substituted_item)
                else:
                    processed_list.append(item)
            
            # Convert list to tuple for selection coordinates
            if key == 'selection' and len(processed_list) == 2:
                processed_args[key] = tuple(processed_list)
            else:
                processed_args[key] = processed_list
        else:
            processed_args[key] = value
    
    return processed_args

def get_matching_actions(comparison_result):
    actions = []    
    comparison_level = extract_comparison_level(comparison_result["id1"])

    for category_key in comparison_result["result"]["category"].keys():
        # print(comparison_level, category_key)
        rules = load_matching_rules(comparison_level, category_key)

        for rule in rules:
            # print(f"Processing rule: {rule.get('id', 'unknown')}")
            # print(f"Rule condition: {rule.get('condition', {})}")
            
            # Check if rule has parameters (even empty ones)
            if 'parameter' in rule:
                parameters = rule['parameter']
                parameter_combinations = generate_parameter_combinations(parameters, comparison_result)
                # print(f"Generated {len(parameter_combinations)} parameter combinations")

                for param_combo in parameter_combinations:
                    # print(f"Testing parameter combo: {param_combo}")
                    condition_result = evaluate_rule_condition(rule['condition'], comparison_result, param_combo)
                    # print(f"Condition result: {condition_result}")

                    if condition_result:
                        action = rule['action'].copy()
                        print(f"Condition matched! Action: {action}")
                        processed_args = process_action_args(action['args'], param_combo, comparison_result)
                        print(f"Processed args: {processed_args}")
                        print(f"Processed args types: {[(k, type(v)) for k, v in processed_args.items()]}")
                        # breakpoint()

                        if processed_args is not None:
                            action['args'] = processed_args
                            action['_parameters'] = param_combo
                            actions.append(action)
                            print(f"Action added to list. Total actions: {len(actions)}")
            else:
                print("Rule has no parameter field, skipping...")


    
    return actions

if __name__ == "__main__":
    from managers.arc_manager import ARCManager
    from comparison import compare

    # TASK_HEX_CODE = "007bbfb7"
    TASK_HEX_CODE = "08ed6ac7"
    task = ARCManager.from_hex_code(TASK_HEX_CODE)

    pnum = (0, 0)
    gnum = (0, 1)
    onum = (1, 2)
    xnum = (2, 0)
    typ = "object"
    
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

    
    with open(f"comparison_result_{TASK_HEX_CODE}_{typ}.json", "w") as f:
        json.dump(comparison_result, f, indent=2, default=str)
    
    actions = get_matching_actions(comparison_result)

    
    
    