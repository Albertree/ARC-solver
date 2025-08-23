from ARCKG.grid import GRID
from ARCKG.task import TASK
import os
import ast
import json
from .program_optimizer import ProgramOptimizer
from comparison import *

class ARCSolver:
    def __init__(self, task: TASK):
        self.task = task
        self.task_hex_code = task.hex_code
        # self.programs = []  # Store programs for each pair

        # from init_memory import init_memory
        # init_memory(task)

    def solve(self):
        for i, pair in enumerate(self.task.example_pairs):
            print(f"Processing example pair {i} for task {self.task_hex_code}")
            lv1_program = self._generate_level_1_program(pair, i)
            # lv2_program = self._generate_level_2_program(lv1_program, pair, i)
            # lv3_program = self._generate_level_3_program(lv2_program, pair, i)
        
        print(f"Level 1 programs generated for task {self.task_hex_code} in 'solver/result_code'")
        for line in lv1_program:
            print(line)

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

        return program

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


    def play(self):
        for i, pair in enumerate(self.task.childs):
            pair_id = i

            # pair_path = f"memory/TASK_nodes/TASKcomparison/task_{TASK_HEX_CODE}/PAIR_{pair_id}"
            # if not os.path.exists(pair_path):
            #     os.makedirs(pair_path)

        # pair_path = f"memory/comparison/task_{TASK_HEX_CODE}/PAIR_{pair_id}"
        # if not os.path.exists(pair_path):
        #     os.makedirs(pair_path)

            # grid comparison #########################################################
            grid1 = pair.childs[0]
            grid2 = pair.childs[1]

            g_path = f"memory/TASK_nodes/TASK_{self.task_hex_code}/PAIR_edges/PAIR_{pair_id}/GRID"
            if not os.path.exists(g_path):
                os.makedirs(g_path)
            
            print(f"Comparing {grid1.__repr__()} and {grid2.__repr__()}")
            comparison_receipt = compare(grid1, grid2)
            comm_count = count_comm_categories(comparison_receipt)

            with open(f"{g_path}/G_1_{comm_count}.json", "w") as f:
                json.dump(comparison_receipt, f, indent=2)


            # object comparison #########################################################
            o_group1 = grid1.objects
            o_group2 = grid2.objects
            total_o_comparisons = len(o_group1) * len(o_group2)
            o_comparison_count = 0

            o_path = f"memory/TASK_nodes/TASK_{self.task_hex_code}/PAIR_edges/PAIR_{pair_id}/OBJECT"
            if not os.path.exists(o_path):
                os.makedirs(o_path)

            for i, obj1 in enumerate(o_group1):
                for j, obj2 in enumerate(o_group2):
                    o_comparison_count += 1
                    # print(f"Comparing {obj1.__repr__()} and {obj2.__repr__()} ({o_comparison_count}/{total_o_comparisons})")
                    comparison_receipt = compare(obj1, obj2)
                    comm_count = count_comm_categories(comparison_receipt)

                    if comm_count >= 5:
                        with open(f"{o_path}/O_{o_comparison_count}_{comm_count}.json", "w") as f:
                            json.dump(comparison_receipt, f, indent=2)
                    else:
                        pass


            # pixel comparison #########################################################
            x_group1 = grid1.pixels
            x_group2 = grid2.pixels
            total_x_comparisons = len(x_group1) * len(x_group2)
            x_comparison_count = 0

            x_path = f"memory/TASK_nodes/TASK_{self.task_hex_code}/PAIR_edges/PAIR_{pair_id}/PIXEL"
            if not os.path.exists(x_path):
                os.makedirs(x_path)

            for i, pix1 in enumerate(x_group1):
                for j, pix2 in enumerate(x_group2):
                    x_comparison_count += 1
                    # print(f"Comparing {pix1.__repr__()} and {pix2.__repr__()} ({x_comparison_count}/{total_x_comparisons})")
                    comparison_receipt = compare(pix1, pix2)
                    comm_count = count_comm_categories(comparison_receipt)

                    if comm_count >= 1:
                        with open(f"{x_path}/X_{x_comparison_count}_{comm_count}.json", "w") as f:
                            json.dump(comparison_receipt, f, indent=2)
                    else:
                        pass


            # breakpoint()