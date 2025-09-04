"""
Program Management System for ARC Solver

This module provides a comprehensive ProgramManager class that handles all program-related
operations including generation, saving, validation, and execution of ARC solution programs.
"""

import os
import ast
import json
from typing import List, Dict, Any, Optional, Tuple
from ARCKG.task import TASK
from ARCKG.grid import GRID
from ARCKG.tf_grid import TF_GRID
from comparison import compare
from make_rule import get_matching_actions
from DSL.my_apply_DSL import apply_DSL
from DSL.my_transformation_DSL import coloring, make_grid
from DSL.my_selection import SELECTION


class ProgramManager:    
    def __init__(self, task: TASK, base_output_dir: str = "result_code"):
        self.task = task
        self.task_hex_code = task.hex_code
        self.base_output_dir = base_output_dir
        
    # ==================== PROGRAM GENERATION ====================
    
    def generate_program(self, pair, pair_index: int) -> List[str]:
        # Reset TF_GRID ID counter for new pair
        TF_GRID.reset_id_counter()
        
        input_grid = pair.input_grid
        output_grid = pair.output_grid
        
        program = [
            'def solve(input_grid):',
            '    tfg0 = input_grid',
        ]
        tfg_counter = 0
        current_grid_var = f"tfg{tfg_counter}"
        
        # Use rule-based approach to generate actions
        comparison_result = compare(input_grid, output_grid, save=False)
        actions = get_matching_actions(comparison_result)
        
        # Apply actions from rule basket
        for action in actions:
            if 'name' in action and 'args' in action:
                action_name = action['name']
                action_args = action['args']
                
                # Build args string for DSL call
                args_list = []
                for key, value in action_args.items():
                    args_list.append(str(value))
                
                args_str = ", ".join(args_list)
                
                # Generate DSL call with proper tfg counter
                tfg_counter += 1
                next_grid_var = f"tfg{tfg_counter}"
                program.append(f"    {next_grid_var} = apply_DSL({current_grid_var}, {action_name}, {args_str})")
                current_grid_var = next_grid_var
        
        # Fallback to original logic if no rules matched
        if not actions:
            if input_grid.size != output_grid.size:
                most_frequent_color = input_grid.get_most_frequent_color()
                tfg_counter += 1
                next_grid_var = f"tfg{tfg_counter}"
                program.append(f"    {next_grid_var} = apply_DSL({current_grid_var}, make_grid, {output_grid.height}, {output_grid.width}, {most_frequent_color})")
                current_grid_var = next_grid_var
                input_raw_data_for_comparison = [[most_frequent_color for _ in range(output_grid.width)] for _ in range(output_grid.height)]
            else:
                input_raw_data_for_comparison = input_grid.raw_data

            for r in range(output_grid.height):
                for c in range(output_grid.width):
                    input_color = input_raw_data_for_comparison[r][c] if r < len(input_raw_data_for_comparison) and c < len(input_raw_data_for_comparison[0]) else input_grid.get_most_frequent_color()
                    
                    if input_color != output_grid.raw_data[r][c]:
                        tfg_counter += 1
                        next_grid_var = f"tfg{tfg_counter}"
                        program.append(f"    {next_grid_var} = apply_DSL({current_grid_var}, coloring, [({r}, {c})], {output_grid.raw_data[r][c]})")
                        current_grid_var = next_grid_var

        program.append(f"    output_grid = {current_grid_var}")
        program.append(f"    return output_grid")
        
        return program

    def generate_program_with_rules(self, pair, pair_index: int, rules: List[Dict]) -> List[str]:
        # Reset TF_GRID ID counter for new pair
        TF_GRID.reset_id_counter()
        
        input_grid = pair.input_grid
        output_grid = pair.output_grid
        
        program = [
            'def solve(input_grid):',
            '    tfg0 = input_grid',
        ]
        tfg_counter = 0
        current_grid_var = f"tfg{tfg_counter}"
        
        # Apply actions from rule basket
        for action in rules:
            if 'name' in action and 'args' in action:
                action_name = action['name']
                action_args = action['args']
                
                # Build args string for DSL call
                args_list = []
                for key, value in action_args.items():
                    args_list.append(str(value))
                
                args_str = ", ".join(args_list)
                
                # Generate DSL call with proper tfg counter
                tfg_counter += 1
                next_grid_var = f"tfg{tfg_counter}"
                program.append(f"    {next_grid_var} = apply_DSL({current_grid_var}, {action_name}, {args_str})")
                current_grid_var = next_grid_var
        
        # Fallback to original logic if no rules matched
        if not rules:
            if input_grid.size != output_grid.size:
                most_frequent_color = input_grid.get_most_frequent_color()
                tfg_counter += 1
                next_grid_var = f"tfg{tfg_counter}"
                program.append(f"    {next_grid_var} = apply_DSL({current_grid_var}, make_grid, {output_grid.height}, {output_grid.width}, {most_frequent_color})")
                current_grid_var = next_grid_var
                input_raw_data_for_comparison = [[most_frequent_color for _ in range(output_grid.width)] for _ in range(output_grid.height)]
            else:
                input_raw_data_for_comparison = input_grid.raw_data

            for r in range(output_grid.height):
                for c in range(output_grid.width):
                    input_color = input_raw_data_for_comparison[r][c] if r < len(input_raw_data_for_comparison) and c < len(input_raw_data_for_comparison[0]) else input_grid.get_most_frequent_color()
                    
                    if input_color != output_grid.raw_data[r][c]:
                        tfg_counter += 1
                        next_grid_var = f"tfg{tfg_counter}"
                        program.append(f"    {next_grid_var} = apply_DSL({current_grid_var}, coloring, [({r}, {c})], {output_grid.raw_data[r][c]})")
                        current_grid_var = next_grid_var

        program.append(f"    output_grid = {current_grid_var}")
        program.append(f"    return output_grid")
        
        return program

    def generate_and_save_program(self, pair, pair_index: int, level: str = "GRID") -> List[str]:
        """Generate and save a program for a specific pair and level."""
        program = self.generate_program(pair, pair_index)
        self.save_program(program, pair_index, level)
        return program

    # ==================== PROGRAM SAVING ====================
    
    def save_program(self, program: List[str], pair_index: int, level: str = "GRID") -> None:
        """Save the generated program for a specific pair."""
        original_code = "\n".join(program)
        
        # Create level directory
        level_dir = os.path.join(self.base_output_dir, self.task_hex_code, level)
        self.save_code_and_ast(level_dir, f"{self.task_hex_code}_{pair_index}_{level.lower()}", original_code)

    def save_code_and_ast(self, output_dir: str, base_filename: str, code: str) -> None:
        """Save both the Python code and its AST representation."""
        # Save the Python code
        os.makedirs(output_dir, exist_ok=True)
        file_path_code = os.path.join(output_dir, f"{base_filename}.py")
        with open(file_path_code, "w") as f:
            f.write(code)
            
        # Generate and save the AST
        tree = ast.parse(code)
        ast_dict = self.ast_to_dict(tree)
        
        output_dir_ast = os.path.join(output_dir, "ast")
        os.makedirs(output_dir_ast, exist_ok=True)
        file_path_ast = os.path.join(output_dir_ast, f"{base_filename}.json")
        with open(file_path_ast, "w") as f:
            json.dump(ast_dict, f, indent=4)

    # ==================== PROGRAM EXECUTION ====================
    
    def execute_program(self, program_path: str, input_grid: GRID) -> Optional[GRID]:
        """Execute a program file and return the generated output."""
        # Read the program file
        with open(program_path, 'r') as f:
            program_code = f.read()
        
        print(f"Original program code:")
        print(program_code)
        
        # Add import statements and wrap the code
        wrapped_code = f"""
from DSL.my_apply_DSL import apply_DSL
from DSL.my_transformation_DSL import coloring, make_grid
from DSL.my_selection import SELECTION

{program_code}
"""
        
        print(f"Wrapped code:")
        print(wrapped_code)
        
        # Execute the wrapped code
        exec_globals = {
            'input_grid': input_grid,
            'apply_DSL': apply_DSL,
            'coloring': coloring,
            'make_grid': make_grid,
            'SELECTION': SELECTION
        }
        
        print(f"Before exec - exec_globals keys: {list(exec_globals.keys())}")
        
        exec(wrapped_code, exec_globals)
        
        print(f"After exec - exec_globals keys: {list(exec_globals.keys())}")
        
        # Try to get solve function and call it directly
        if 'solve' in exec_globals:
            result = exec_globals['solve'](input_grid)
            return result
        elif 'output_grid' in exec_globals:
            return exec_globals['output_grid']
        else:
            return None

    def execute_saved_program(self, pair_index: int, level: str = "GRID") -> Optional[GRID]:
        if not self.program_exists(pair_index, level):
            return None
        
        pair = self.task.example_pairs[pair_index]
        program_path = self.get_program_file_path(pair_index, level)
        return self.execute_program(program_path, pair.input_grid)

    # ==================== PROGRAM VALIDATION ====================
    
    def validate_program(self, level: str = "GRID") -> List[Dict[str, Any]]:
        """Apply programs from specified level folder and return outputs."""
        result_code_dir = self.base_output_dir
        if not os.path.exists(result_code_dir):
            return []
        
        task_dir = os.path.join(result_code_dir, self.task_hex_code)
        if not os.path.exists(task_dir):
            return []
        
        level_dir = os.path.join(task_dir, level)
        if not os.path.exists(level_dir):
            return []
        
        py_files = [f for f in os.listdir(level_dir) 
                   if f.endswith(".py") and not f.startswith("__")]
        
        if not py_files:
            return []
        
        outputs = []
        
        for filename in sorted(py_files):
            try:
                parts = filename.replace(".py", "").split("_")
                if len(parts) >= 2:
                    pair_number = int(parts[1])
                else:
                    continue
                
                if pair_number >= len(self.task.example_pairs):
                    continue
                
                pair = self.task.example_pairs[pair_number]
                input_grid = pair.input_grid
                
                output = self.execute_program(os.path.join(level_dir, filename), input_grid)
                
                if output is not None:
                    outputs.append({
                        'filename': filename,
                        'pair_number': pair_number,
                        'input_grid': input_grid,
                        'output': output
                    })
                    
            except Exception as e:
                pass

        return outputs

    # ==================== UTILITY METHODS ====================
    
    def get_program_file_path(self, pair_index: int, level: str = "GRID") -> str:
        """Get the file path for a program at a specific level and pair index."""
        return os.path.join(
            self.base_output_dir, 
            self.task_hex_code, 
            level, 
            f"{self.task_hex_code}_{pair_index}_{level.lower()}.py"
        )

    def program_exists(self, pair_index: int, level: str = "GRID") -> bool:
        """Check if a program file exists for a specific pair and level."""
        return os.path.exists(self.get_program_file_path(pair_index, level))

    def load_program(self, pair_index: int, level: str = "GRID") -> Optional[str]:
        """Load a program file for a specific pair and level."""
        file_path = self.get_program_file_path(pair_index, level)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        return None

    def ast_to_dict(self, node) -> Dict[str, Any]:
        """Recursively convert an AST node to a dictionary."""
        if not isinstance(node, ast.AST):
            if isinstance(node, list):
                return [self.ast_to_dict(n) for n in node]
            return node
        
        fields = {
            'node_type': node.__class__.__name__
        }
        for field, value in ast.iter_fields(node):
            fields[field] = self.ast_to_dict(value)
        return fields