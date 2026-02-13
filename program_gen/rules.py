"""
Rule-based matching: comparison result -> DSL actions.
Loads rules from DSL_activation_rule/, evaluates conditions, returns action list.
"""

import json
import os


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
    rule_basket_dir = "DSL_activation_rule"
    rules = []

    if not os.path.exists(rule_basket_dir):
        return rules

    for filename in os.listdir(rule_basket_dir):
        if filename.endswith('.json'):
            parts = filename.split('.json')[0].split('_')
            if len(parts) >= 2:
                file_level = parts[0]
                file_category = parts[1]
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
                if parameters:
                    operand1_path = substitute_parameters(operand1_path, parameters)
                operand1 = get_nested_value(comparison_result, operand1_path)
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
                        pass
                if condition['operator'] == '==':
                    return operand1 == operand2
                return operand1 != operand2
            elif condition['operator'] == 'AND':
                left = evaluate_rule_condition(condition['operand1'], comparison_result, parameters)
                right = evaluate_rule_condition(condition['operand2'], comparison_result, parameters)
                return left and right
            elif condition['operator'] == 'OR':
                left = evaluate_rule_condition(condition['operand1'], comparison_result, parameters)
                right = evaluate_rule_condition(condition['operand2'], comparison_result, parameters)
                return left or right
    return False


def substitute_parameters(text, parameters):
    if not isinstance(text, str) or not parameters:
        return text
    result = text
    for param_name, param_value in parameters.items():
        result = result.replace(f"{{{param_name}}}", str(param_value))
    return result


def get_nested_value(data, path):
    keys = path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict):
            if key in current:
                current = current[key]
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
    value = get_nested_value(data, path)
    if value is None:
        return None
    if isinstance(value, dict):
        if 'comp2' in value:
            return value['comp2']
        if 'comp1' in value:
            return value['comp1']
        return value
    return value


def find_color_with_true_comp2(data, color_category_path):
    color_category = get_nested_value(data, color_category_path)
    if not isinstance(color_category, dict):
        return None
    for color_num in range(10):
        color_key = str(color_num)
        if color_key in color_category:
            color_data = color_category[color_key]
            if isinstance(color_data, dict) and color_data.get('comp2') is True:
                return color_num
    return None


def generate_parameter_combinations(parameters, comparison_result=None):
    if not parameters:
        return [{}]
    import itertools
    param_names = list(parameters.keys())
    param_values = []
    for param_name in param_names:
        param_config = parameters[param_name]
        if param_config.get('type') == 'integer' and 'range' in param_config:
            start, end = param_config['range']
            param_values.append(list(range(start, end + 1)))
        elif param_config.get('type') == 'string' and 'values' in param_config:
            param_values.append(param_config['values'])
        else:
            param_values.append([param_config.get('default', None)])
    combinations = []
    for combo in itertools.product(*param_values):
        combination = {param_names[i]: combo[i] for i in range(len(param_names))}
        if comparison_result is not None:
            should_include = True
            for param_name in param_names:
                param_config = parameters[param_name]
                if 'condition' in param_config:
                    if not evaluate_rule_condition(param_config['condition'], comparison_result, combination):
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
                if actual_value is None:
                    return None
                if key == 'selection' and isinstance(actual_value, dict) and 'category' in actual_value and 'col_index' in actual_value['category'] and 'row_index' in actual_value['category']:
                    col_index = actual_value['category']['col_index']
                    row_index = actual_value['category']['row_index']
                    col_val = col_index.get('comp2', col_index.get('comp1', col_index)) if isinstance(col_index, dict) else col_index
                    row_val = row_index.get('comp2', row_index.get('comp1', row_index)) if isinstance(row_index, dict) else row_index
                    processed_args[key] = [(row_val, col_val)]
                else:
                    processed_args[key] = actual_value
            else:
                if key == 'color' and substituted_value.isdigit():
                    if 'method' in comparison_result.get('result', {}).get('category', {}):
                        true_color = find_color_with_true_comp2(comparison_result, "result.category.color.category")
                        processed_args[key] = true_color if true_color is not None else int(substituted_value)
                    else:
                        processed_args[key] = int(substituted_value)
                else:
                    processed_args[key] = substituted_value
        elif isinstance(value, list):
            processed_list = []
            for item in value:
                if isinstance(item, str):
                    substituted_item = substitute_parameters(item, param_combo)
                    if substituted_item.startswith('result.'):
                        actual_value = get_usable_value_from_comparison_result(comparison_result, substituted_item)
                        if actual_value is None:
                            return None
                        processed_list.append(actual_value)
                    else:
                        processed_list.append(substituted_item)
                else:
                    processed_list.append(item)
            processed_args[key] = tuple(processed_list) if key == 'selection' and len(processed_list) == 2 else processed_list
        else:
            processed_args[key] = value
    return processed_args


def get_matching_actions(comparison_result):
    actions = []
    comparison_level = extract_comparison_level(comparison_result["id1"])
    for category_key in comparison_result["result"]["category"].keys():
        rules = load_matching_rules(comparison_level, category_key)
        for rule in rules:
            if 'parameter' not in rule:
                continue
            parameters = rule['parameter']
            for param_combo in generate_parameter_combinations(parameters, comparison_result):
                if not evaluate_rule_condition(rule['condition'], comparison_result, param_combo):
                    continue
                action = rule['action'].copy()
                processed_args = process_action_args(action['args'], param_combo, comparison_result)
                if processed_args is not None:
                    action['args'] = processed_args
                    action['_parameters'] = param_combo
                    actions.append(action)
    return actions


if __name__ == "__main__":
    from managers.arc_manager import ARCManager
    from ARCKG import compare

    TASK_HEX_CODE = "08ed6ac7"
    task = ARCManager.from_hex_code(TASK_HEX_CODE)
    input_grid = task.example_pairs[0].input_grid
    output_grid = task.example_pairs[0].output_grid
    comparison_result = compare(input_grid, output_grid, save=False)
    with open(f"comparison_result_{TASK_HEX_CODE}_grid.json", "w") as f:
        json.dump(comparison_result, f, indent=2, default=str)
    actions = get_matching_actions(comparison_result)
    print(f"Matched {len(actions)} actions")
