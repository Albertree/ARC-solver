"""
Program manager: rule-based code generation, save, load, execute.
"""

import os
import ast
import json
from typing import List, Dict, Any, Optional

from ARCKG.task import TASK
from ARCKG.grid import GRID
from ARCKG.tf_grid import TF_GRID
from ARCKG import compare
from program_gen.rules import get_matching_actions
from DSL.apply import apply_DSL
from DSL.transformation import coloring, make_grid
from DSL.util import add_added_color, add_removed_color
from DSL.selection import SELECTION


def _action_args_to_kwargs_str(action_args: Dict) -> str:
    """Build kwargs string for a DSL call from action args (shared by generate_*)."""
    kwargs_list = []
    for key, value in action_args.items():
        if isinstance(value, tuple):
            kwargs_list.append(f"{key}={str(value)}")
        elif isinstance(value, dict):
            if key == 'selection' and 'category' in value and 'col_index' in value.get('category') and 'row_index' in value.get('category'):
                col_index = value['category']['col_index']
                row_index = value['category']['row_index']
                col_val = col_index.get('comp2', col_index.get('comp1', col_index)) if isinstance(col_index, dict) else col_index
                row_val = row_index.get('comp2', row_index.get('comp1', row_index)) if isinstance(row_index, dict) else row_index
                kwargs_list.append(f"{key}=[({row_val}, {col_val})]")
            else:
                v = value.get('comp2', value.get('comp1', value))
                kwargs_list.append(f"{key}={str(v)}")
        else:
            kwargs_list.append(f"{key}={str(value)}")
    return ", ".join(kwargs_list)


class ProgramManager:
    def __init__(self, base_output_dir: str = "outputs/generated_codes"):
        self.base_output_dir = base_output_dir

    def generate_program(self, pair, pair_index: int) -> List[str]:
        TF_GRID.reset_id_counter()
        input_grid = pair.input_grid
        output_grid = pair.output_grid

        def base_structure():
            return ['def solve(input_grid):', '    added_color = []', '    removed_color = []', '    tfg0 = input_grid']

        def wrapper_end(tfg_var):
            return [f'    output_grid = {tfg_var}', '    return output_grid']

        program = base_structure()
        tfg_counter = 0
        current_grid_var = "tfg0"
        comparison_result = compare(input_grid, output_grid, save=False)
        actions = get_matching_actions(comparison_result)

        for action in actions:
            if 'name' not in action or 'args' not in action:
                continue
            kwargs_str = _action_args_to_kwargs_str(action['args'])
            tfg_counter += 1
            next_grid_var = f"tfg{tfg_counter}"
            program.append(f"    {next_grid_var} = apply_DSL({current_grid_var}, {action['name']}, {kwargs_str})")
            current_grid_var = next_grid_var

        program.extend(wrapper_end(current_grid_var))
        return program

    def generate_program_with_rules(self, pair, pair_index: int, rules: List[Dict], base_program: List[str] = None) -> List[str]:
        TF_GRID.reset_id_counter()
        input_grid = pair.input_grid
        output_grid = pair.output_grid

        def base_structure():
            return ['def solve(input_grid):', '    added_color = []', '    removed_color = []', '    tfg0 = input_grid']

        def wrapper_end(tfg_var):
            return [f'    output_grid = {tfg_var}', '    return output_grid']

        program = base_structure()
        tfg_counter = 0
        current_grid_var = "tfg0"

        if base_program:
            modification_lines = []
            in_section = False
            for line in base_program:
                s = line.strip()
                if s == 'tfg0 = input_grid':
                    in_section = True
                    continue
                if s.startswith('output_grid = tfg') or s == 'return output_grid':
                    in_section = False
                    continue
                if in_section and 'tfg' in line and '=' in line:
                    modification_lines.append(line)
                    parts = line.split('tfg')
                    if len(parts) > 1:
                        num_part = parts[1].split()[0]
                        if num_part.isdigit():
                            tfg_counter = max(tfg_counter, int(num_part))
            program.extend(modification_lines)
            current_grid_var = f"tfg{tfg_counter}"

        for action in rules:
            if 'name' not in action or 'args' not in action:
                continue
            kwargs_str = _action_args_to_kwargs_str(action['args'])
            tfg_counter += 1
            next_grid_var = f"tfg{tfg_counter}"
            program.append(f"    {next_grid_var} = apply_DSL({current_grid_var}, {action['name']}, {kwargs_str})")
            current_grid_var = next_grid_var

        program.extend(wrapper_end(current_grid_var))
        return program

    def generate_and_save_program(self, pair, pair_index: int, level: str = "GRID", task_hex_code: str = None) -> List[str]:
        program = self.generate_program(pair, pair_index)
        self.save_program(program, pair_index, level, task_hex_code)
        return program

    def save_program(self, program: List[str], pair_index: int, level: str = "GRID", task_hex_code: str = None) -> None:
        original_code = "\n".join(program)
        level_dir = os.path.join(self.base_output_dir, task_hex_code, level)
        self.save_code_and_ast(level_dir, f"{task_hex_code}_{pair_index}_{level.lower()}", original_code)

    def save_code_and_ast(self, output_dir: str, base_filename: str, code: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, f"{base_filename}.py"), "w") as f:
            f.write(code)
        tree = ast.parse(code)
        ast_dir = os.path.join(output_dir, "ast")
        os.makedirs(ast_dir, exist_ok=True)
        with open(os.path.join(ast_dir, f"{base_filename}.json"), "w") as f:
            json.dump(self.ast_to_dict(tree), f, indent=4)

    def execute_program(self, program_path: str, input_grid: GRID) -> Optional[GRID]:
        with open(program_path, 'r') as f:
            program_code = f.read()
        wrapped_code = f"""
from DSL.apply import apply_DSL
from DSL.transformation import coloring, make_grid
from DSL.selection import SELECTION
from DSL.util import add_added_color, add_removed_color

{program_code}
"""
        exec_globals = {
            'input_grid': input_grid,
            'apply_DSL': apply_DSL,
            'coloring': coloring,
            'make_grid': make_grid,
            'add_added_color': add_added_color,
            'add_removed_color': add_removed_color,
            'SELECTION': SELECTION
        }
        exec(wrapped_code, exec_globals)
        if 'solve' in exec_globals:
            return exec_globals['solve'](input_grid)
        if 'output_grid' in exec_globals:
            return exec_globals['output_grid']
        return None

    def execute_saved_program(self, pair_index: int, level: str = "GRID", task_hex_code: str = None) -> Optional[GRID]:
        if not self.program_exists(pair_index, level, task_hex_code):
            return None
        from managers.arc_manager import ARCManager
        task = ARCManager.from_hex_code(task_hex_code)
        pair = task.example_pairs[pair_index]
        program_path = self.get_program_file_path(pair_index, level, task_hex_code)
        return self.execute_program(program_path, pair.input_grid)

    def validate_program(self, level: str = "GRID", task_hex_code: str = None, task: TASK = None) -> List[Dict[str, Any]]:
        """Run all programs in the level folder. Requires task_hex_code and task (or set on instance)."""
        if task_hex_code is None:
            task_hex_code = getattr(self, 'task_hex_code', None)
        if task is None:
            task = getattr(self, 'task', None)
        if task_hex_code is None or task is None:
            return []
        result_code_dir = self.base_output_dir
        task_dir = os.path.join(result_code_dir, task_hex_code)
        level_dir = os.path.join(task_dir, level)
        if not os.path.exists(level_dir):
            return []
        py_files = [f for f in os.listdir(level_dir) if f.endswith(".py") and not f.startswith("__")]
        if not py_files:
            return []
        outputs = []
        for filename in sorted(py_files):
            try:
                parts = filename.replace(".py", "").split("_")
                if len(parts) < 2:
                    continue
                pair_number = int(parts[1])
                if pair_number >= len(task.example_pairs):
                    continue
                pair = task.example_pairs[pair_number]
                output = self.execute_program(os.path.join(level_dir, filename), pair.input_grid)
                if output is not None:
                    outputs.append({'filename': filename, 'pair_number': pair_number, 'input_grid': pair.input_grid, 'output': output})
            except Exception:
                pass
        return outputs

    def get_program_file_path(self, pair_index: int, level: str = "GRID", task_hex_code: str = None) -> str:
        return os.path.join(
            self.base_output_dir,
            task_hex_code,
            level,
            f"{task_hex_code}_{pair_index}_{level.lower()}.py"
        )

    def program_exists(self, pair_index: int, level: str = "GRID", task_hex_code: str = None) -> bool:
        return os.path.exists(self.get_program_file_path(pair_index, level, task_hex_code))

    def load_program(self, pair_index: int, level: str = "GRID", task_hex_code: str = None) -> Optional[str]:
        path = self.get_program_file_path(pair_index, level, task_hex_code)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read()
        return None

    def ast_to_dict(self, node) -> Dict[str, Any]:
        if not isinstance(node, ast.AST):
            if isinstance(node, list):
                return [self.ast_to_dict(n) for n in node]
            return node
        return {
            'node_type': node.__class__.__name__,
            **{k: self.ast_to_dict(v) for k, v in ast.iter_fields(node)}
        }
