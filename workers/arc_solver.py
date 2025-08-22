from ARCKG.grid import GRID
from ARCKG.task import TASK
import os
import ast
import json
from .program_optimizer import ProgramOptimizer

class ARCSolver:
    def __init__(self, task: TASK):
        self.task = task
        self.task_hex_code = task.hex_code
        self.programs = []  # Store programs for each pair

    def solve(self):
        for i, pair in enumerate(self.task.example_pairs):
            print(f"Processing example pair {i} for task {self.task_hex_code}")
            self._generate_level_1_program(pair, i)
        
        print(f"Level 1 programs generated for task {self.task_hex_code} in 'solver/result_code'")

    def _generate_level_1_program(self, pair, pair_index: int):
        """Solve a single input/output grid pair"""
        input_grid = pair.input_grid
        output_grid = pair.output_grid
        
        program = [
            'def solve(input_grid):',
            '    tfg0 = input_grid',
        ]
        tfg_counter = 0
        current_grid_var = f"tfg{tfg_counter}"
        
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

        self._save_program(program, pair_index)

        breakpoint()

    def ast_to_dict(self, node):
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

    def _save_program(self, program, pair_index: int):
        """Save the generated program for a specific pair"""
        original_code = "\n".join(program)
        
        # Level 1
        level1_dir = os.path.join(os.path.dirname(__file__), "..", "result_code", self.task_hex_code, "level-1")
        self._save_code_and_ast(level1_dir, f"{self.task_hex_code}_{pair_index}_lv1", original_code)

        # # Level 2 - Commented out
        # optimizer_lv2 = ProgramOptimizer(original_code)
        # optimized_lv2 = {
        #     "color": optimizer_lv2.optimize_by_color(),
        #     "row": optimizer_lv2.optimize_by_row(),
        #     "col": optimizer_lv2.optimize_by_column()
        # }
        # level2_dir = os.path.join(os.path.dirname(__file__), "..", "result_code", self.task_hex_code, "level-2")
        # for opt_type, code in optimized_lv2.items():
        #     self._save_code_and_ast(level2_dir, f"{self.task_hex_code}_{pair_index}_lv2-{opt_type}", code)

        # # Level 3 - Commented out
        # level3_dir = os.path.join(os.path.dirname(__file__), "..", "result_code", self.task_hex_code, "level-3")
        # for opt_type, code in optimized_lv2.items():
        #     optimizer_lv3 = ProgramOptimizer(code, self.task.example_pairs[pair_index].input_grid)
        #     optimized_code_lv3 = optimizer_lv3.optimize_with_objects(code)
        #     self._save_code_and_ast(level3_dir, f"{self.task_hex_code}_{pair_index}_lv3-{opt_type}", optimized_code_lv3)


    def _save_code_and_ast(self, output_dir, base_filename, code):
        """Helper to save both the .py and .json AST file."""
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