from ARCKG.grid import GRID
from ARCKG.task import TASK
import os
import ast
import json
from .program_optimizer import ProgramOptimizer
from comparison import *
from .solver_utils import *

class ARCSolver:
    def __init__(self, task: TASK):
        self.task = task
        self.task_hex_code = task.hex_code
        # self.programs = []  # Store programs for each pair

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
        # Clean up existing comparison directory
        comparison_base_path = "comparison"
        if os.path.exists(comparison_base_path):
            import shutil
            shutil.rmtree(comparison_base_path)
            print(f"Cleaned up existing comparison directory: {comparison_base_path}")
        
        for i, pair in enumerate(self.task.childs):
            pair_id = i

            # grid comparison #########################################################
            grid1 = pair.childs[0]
            grid2 = pair.childs[1]

            g_path = f"comparison/TASK_nodes/TASK_{self.task_hex_code}/PAIR_edges/PAIR_{pair_id}/GRID"
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

            o_path = f"comparison/TASK_nodes/TASK_{self.task_hex_code}/PAIR_edges/PAIR_{pair_id}/OBJECT"
            if not os.path.exists(o_path):
                os.makedirs(o_path)

            for i, obj1 in enumerate(o_group1):
                for j, obj2 in enumerate(o_group2):
                    o_comparison_count += 1
                    print(f"Comparing {obj1.__repr__()} and {obj2.__repr__()} ({o_comparison_count}/{total_o_comparisons})")
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

            x_path = f"comparison/TASK_nodes/TASK_{self.task_hex_code}/PAIR_edges/PAIR_{pair_id}/PIXEL"
            if not os.path.exists(x_path):
                os.makedirs(x_path)

            for i, pix1 in enumerate(x_group1):
                for j, pix2 in enumerate(x_group2):
                    x_comparison_count += 1
                    print(f"Comparing {pix1.__repr__()} and {pix2.__repr__()} ({x_comparison_count}/{total_x_comparisons})")
                    comparison_receipt = compare(pix1, pix2)
                    comm_count = count_comm_categories(comparison_receipt)

                    if comm_count >= 1:
                        # Create score-based subfolder
                        score_path = os.path.join(x_path, str(comm_count))
                        if not os.path.exists(score_path):
                            os.makedirs(score_path)
                        
                        # For score 1, create additional subfolders based on color and coordinate results
                        if comm_count == 1:
                            # Check color and coordinate results
                            color_result = "COMM" if comparison_receipt["category"]["color"]["color"]["type"] == "COMM" else "DIFF"
                            coordinate_result = "COMM" if comparison_receipt["category"]["coordinate"]["row"]["type"] == "COMM" and comparison_receipt["category"]["coordinate"]["col"]["type"] == "COMM" else "DIFF"
                            
                            # Create subfolder name based on results
                            subfolder_name = f"color_{color_result}_coord_{coordinate_result}"
                            final_path = os.path.join(score_path, subfolder_name)
                        else:
                            final_path = score_path
                        
                        if not os.path.exists(final_path):
                            os.makedirs(final_path)
                        
                        with open(f"{final_path}/X_{x_comparison_count}_{comm_count}.json", "w") as f:
                            json.dump(comparison_receipt, f, indent=2)
                    else:
                        pass


        
    def temp_solve(self):
        spacing1 = " " * 4
        spacing2 = " " * 8
        spacing3 = " " * 12
        spacing4 = " " * 16



        print("Start")
        print("Inter-TASK Analysis")
        for _ in range(1):
            print("    nothing")
        print()

        print("Intra-TASK Analysis (T1, T2, T3, T4)") # 특징, 객체, 변화 존재 여부의 공통성(COMM) 중심으로 공통적인 부분을 찾는 것이 목표
        print("Intra-TASK Inter-PAIR Analysis (T1)")
        for pair_idx, pair in enumerate(self.task.example_pairs):
            if is_empty_program(pair.program):
                print(f"{spacing1}PAIR {pair_idx} has no program -> Do deeper analysis of a PAIR to make program")
                print(f"{spacing2}Intra-PAIR Analysis (P1, P2, P3)")
                print(f"{spacing2}Inter-GRID Analysis (P1)")
                print(f"{spacing3}Comparing {pair.input_grid.__repr__()} and {pair.output_grid.__repr__()}")
                print(f"{spacing3}GRID-level comparison result is Size: COMM, Color: DIFF, AREA: DIFF, Symmetry: DIFF")
                print(f"{spacing3}Applying deep GRID knowledge to program...")
                print(f"{spacing3}Not enough information to make program -> Do deeper analysis of a PAIR to make program")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Inter-OBJECT Analysis (P2)")
                print(f"{spacing3}Comparing {len(pair.childs[0].objects)} objects in input grid and {len(pair.childs[1].objects)} objects in output grid")
                print(f"{spacing3}Total {len(pair.childs[0].objects) * len(pair.childs[1].objects)} object comparisons")
                for obj_idx_i, obj_i in enumerate(pair.childs[0].objects):
                    for obj_idx_o, obj_o in enumerate(pair.childs[1].objects):
                        print(f"{spacing3}Comparing OBJECT {obj_idx_i.__repr__()} and {obj_idx_o.__repr__()}")
                        print(f"{spacing3}OBJECT-level comparison result is Size: COMM, Color: DIFF, Method: DIFF ...")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Completed OBJECT Comparisons, Analyzing the comparison results...")
                print(f"{spacing2}Prioritizing based on symbolic distance...")
                print(f"{spacing2}Generating a program...")
                print(f"{spacing2}Program generated!")
                print(f"{spacing2}Validating the program...")
                print(f"{spacing2}Program is invalid -> Do deeper analysis of a PAIR to make program")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Inter-PIXEL Analysis (P3)")
                print(f"{spacing3}Comparing {len(pair.childs[0].pixels)} pixels in input grid and {len(pair.childs[1].pixels)} pixels in output grid")
                print(f"{spacing3}Total {len(pair.childs[0].pixels) * len(pair.childs[1].pixels)} pixel comparisons")
                for pix_idx_i, pix_i in enumerate(pair.childs[0].pixels):
                    for pix_idx_o, pix_o in enumerate(pair.childs[1].pixels):
                        print(f"{spacing3}Comparing PIXEL {pix_idx_i.__repr__()} and {pix_idx_o.__repr__()}")
                        print(f"{spacing3}PIXEL-level comparison result is Color: COMM, Coordinate: DIFF")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Completed PIXEL Comparisons, Analyzing the comparison results...")
                print(f"{spacing2}Prioritizing based on symbolic distance...")
                print(f"{spacing2}Generating a program...")
                print(f"{spacing2}Program generated!")
                print(f"{spacing2}Validating the program on this PAIR...")
                print(f"{spacing2}Program is valid on this PAIR!")
                print(f"{spacing2}Validating the program on other PAIRS...")
                print(f"{spacing2}Program is valid on NONE in {self.task.example_pair_count - 1} PAIRs -> Apply Abstraction to generalize the program")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Intra-GRID Inter-Pixel Analysis (G2)")
                print(f"{spacing3}Comparing {len(pair.childs[0].pixels)} PIXELs in {pair.input_grid.__repr__()}.")
                print(f"{spacing3}Total {len(pair.childs[0].pixels) * len(pair.childs[0].pixels)-1} pixel comparisons")
                for pix_idx_1, pix_1 in enumerate(pair.childs[0].pixels):
                    for pix_idx_2, pix_2 in enumerate(pair.childs[0].pixels):
                        print(f"{spacing3}Comparing PIXEL {pix_1.__repr__()} and {pix_2.__repr__()}.")
                        print(f"{spacing3}PIXEL-level comparison result is Color: COMM, Coordinate: DIFF")
                print()
                input("Press Enter to continue...")
                print(f"{spacing3}Comparing {len(pair.childs[1].pixels)} PIXELs in {pair.output_grid.__repr__()}.")
                print(f"{spacing3}Total {len(pair.childs[1].pixels) * len(pair.childs[1].pixels)-1} pixel comparisons")
                for pix_idx_1, pix_1 in enumerate(pair.childs[1].pixels):
                    for pix_idx_2, pix_2 in enumerate(pair.childs[1].pixels):
                        print(f"{spacing3}Comparing PIXEL {pix_1.__repr__()} and {pix_2.__repr__()}.")
                        print(f"{spacing3}PIXEL-level comparison result is Color: COMM, Coordinate: DIFF")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Completed PIXEL Comparisons, Analyzing the comparison results...")
                print(f"{spacing2}Grouping based on Commonalities...")
                print(f"{spacing2}Generating a program...")
                print(f"{spacing2}Program generated!")
                print(f"{spacing2}Validating the program on this PAIR...")
                print(f"{spacing2}Program is valid on this PAIR!")
                print(f"{spacing2}Validating the program on other PAIRS...")
                print(f"{spacing2}Program is valid on NONE in {self.task.example_pair_count - 1} PAIRs -> Apply Abstraction to generalize the program")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Intra-GRID Inter-Object Analysis (G1)")
                print(f"{spacing3}Comparing {len(pair.childs[0].objects)} OBJECTs in {pair.input_grid.__repr__()}.")
                print(f"{spacing3}Total {len(pair.childs[0].objects) * len(pair.childs[0].objects)-1} object comparisons")
                for obj_idx_1, obj_1 in enumerate(pair.childs[0].objects):
                    for obj_idx_2, obj_2 in enumerate(pair.childs[0].objects):
                        print(f"{spacing3}Comparing OBJECT {obj_1.__repr__()} and {obj_2.__repr__()}.")
                        print(f"{spacing3}OBJECT-level comparison result is Size: COMM, Color: DIFF, AREA: DIFF, Symmetry: DIFF")
                print()
                input("Press Enter to continue...")
                print(f"{spacing3}Comparing {len(pair.childs[1].objects)} OBJECTs in {pair.output_grid.__repr__()}.")
                print(f"{spacing3}Total {len(pair.childs[1].objects) * len(pair.childs[1].objects)-1} object comparisons")
                for obj_idx_1, obj_1 in enumerate(pair.childs[1].objects):
                    for obj_idx_2, obj_2 in enumerate(pair.childs[1].objects):
                        print(f"{spacing3}Comparing OBJECT {obj_1.__repr__()} and {obj_2.__repr__()}.")
                        print(f"{spacing3}OBJECT-level comparison result is Size: COMM, Color: DIFF, AREA: DIFF, Symmetry: DIFF")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Completed OBJECT Comparisons, Analyzing the comparison results...")
                print(f"{spacing2}Grouping based on Commonalities...")
                print(f"{spacing2}Generating a program...")
                print(f"{spacing2}Program generated!")
                print(f"{spacing2}Validating the program on this PAIR...")
                print(f"{spacing2}Program is valid on this PAIR!")
                print(f"{spacing2}Validating the program on other PAIRS...")
                print(f"{spacing2}Program is valid on NONE in {self.task.example_pair_count - 1} PAIRs -> Apply Abstraction to generalize the program")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Intra-OBJECT Inter-Pixel Analysis (O1)")
                print(f"{spacing3}Comparing PIXELs in OBJECTs in {pair.input_grid.__repr__()}.")
                for obj in pair.childs[0].objects:
                    print(f"{spacing3}Comparing {len(obj.pixels)} PIXELs in {obj.__repr__()}.")
                    print(f"{spacing3}Total {len(obj.pixels) * len(obj.pixels)-1} pixel comparisons")
                    for pix_idx_1, pix_1 in enumerate(obj.pixels):
                        for pix_idx_2, pix_2 in enumerate(obj.pixels):
                            print(f"{spacing3}Comparing PIXEL {pix_1.__repr__()} and {pix_2.__repr__()}.")
                            print(f"{spacing3}PIXEL-level comparison result is Color: COMM, Coordinate: DIFF")
                print(f"{spacing2}Completed Inter-PIXEL Comparisons in all OBJECTs in input grid, Analyzing the comparison results...")
                print()
                input("Press Enter to continue...")
                print(f"{spacing3}Comparing PIXELs in OBJECTs in {pair.output_grid.__repr__()}.")
                for obj in pair.childs[1].objects:
                    print(f"{spacing3}Comparing {len(obj.pixels)} PIXELs in {obj.__repr__()}.")
                    print(f"{spacing3}Total {len(obj.pixels) * len(obj.pixels)-1} pixel comparisons")
                    for pix_idx_1, pix_1 in enumerate(obj.pixels):
                        for pix_idx_2, pix_2 in enumerate(obj.pixels):
                            print(f"{spacing3}Comparing PIXEL {pix_1.__repr__()} and {pix_2.__repr__()}.")
                            print(f"{spacing3}PIXEL-level comparison result is Color: COMM, Coordinate: DIFF")
                print(f"{spacing2}Completed Inter-PIXEL Comparisons in all OBJECTs in output grid, Analyzing the comparison results...")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Analyzing the comparison results...")
                print(f"{spacing2}Prioritizing based on symbolic distance...")
                print(f"{spacing2}Searching for meaningful relations...")
                print(f"{spacing2}Generating a program...")
                print(f"{spacing2}Program generated!")
                print(f"{spacing2}Validating the program on this PAIR...")
                print(f"{spacing2}Program is valid on this PAIR!")
                print(f"{spacing2}Validating the program on other PAIRS...")
                print(f"{spacing2}Program is valid on NONE in {self.task.example_pair_count - 1} PAIRs -> Apply Abstraction to generalize the program")
                print()
                input("Press Enter to continue...")                

                print("----------------------------------------------------")
                print(f"With Current level of Intra-PAIR Analysis, we cannot make a program that works on other PAIRs.")
                print(f"Need to see other PAIRs more deeply to make a program that works on other PAIRs.")
                print()
                input("Press Enter to continue...")
                print(f"{spacing1}Inter-PAIR Analysis (T1, T2, T3, T4)")
                print(f"{spacing2}Inter-PAIR GRID Analysis (T2)")
                next_pair_idx = pair_idx + 1
                if next_pair_idx >= self.task.example_pair_count:
                    next_pair_idx = 0
                    break
                next_pair = self.task.example_pairs[next_pair_idx]
                print(f"{spacing3}Comparing {pair.input_grid.__repr__()} and {next_pair.input_grid.__repr__()}")
                print(f"{spacing3}GRID-level comparison result is Size: COMM, Color: DIFF, AREA: DIFF, Symmetry: DIFF")
                print(f"{spacing3}Comparing {pair.output_grid.__repr__()} and {next_pair.output_grid.__repr__()}")
                print(f"{spacing3}GRID-level comparison result is Size: COMM, Color: DIFF, AREA: DIFF, Symmetry: DIFF")
                print(f"{spacing3}Applying deep GRID knowledge to program...")
                print(f"{spacing3}Program generated!")
                print(f"{spacing3}Validating the program on this PAIR...")
                print(f"{spacing3}Program is valid on this PAIR!")
                print(f"{spacing3}Validating the program on other PAIRS...")
                print(f"{spacing3}Program is valid on NONE in {self.task.example_pair_count - 1} PAIRs -> Apply Abstraction to generalize the program")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Inter-PAIR OBJECT Analysis (T3)")
                print(f"{spacing3}Comparing {len(pair.childs[0].objects)} OBJECTs in {pair.input_grid.__repr__()} with {len(next_pair.childs[0].objects)} OBJECTs in {next_pair.input_grid.__repr__()}.")
                print(f"{spacing3}Total {len(pair.childs[0].objects) * len(next_pair.childs[0].objects)} object comparisons")
                for obj_idx_1, obj_1 in enumerate(pair.childs[0].objects):
                    for obj_idx_2, obj_2 in enumerate(next_pair.childs[0].objects):
                        print(f"{spacing3}Comparing OBJECT {obj_1.__repr__()} in {pair.input_grid.__repr__()} and {obj_2.__repr__()} in {next_pair.input_grid.__repr__()}.")
                        print(f"{spacing3}OBJECT-level comparison result is Size: COMM, Color: DIFF, AREA: DIFF, Symmetry: DIFF")
                print()
                input("Press Enter to continue...")
                print(f"{spacing3}Comparing {len(pair.childs[1].objects)} OBJECTs in {pair.output_grid.__repr__()} with {len(next_pair.childs[1].objects)} OBJECTs in {next_pair.output_grid.__repr__()}.")
                print(f"{spacing3}Total {len(pair.childs[1].objects) * len(next_pair.childs[1].objects)} object comparisons")
                for obj_idx_1, obj_1 in enumerate(pair.childs[1].objects):
                    for obj_idx_2, obj_2 in enumerate(next_pair.childs[1].objects):
                        print(f"{spacing3}Comparing OBJECT {obj_1.__repr__()} in {pair.output_grid.__repr__()} and {obj_2.__repr__()} in {next_pair.output_grid.__repr__()}.")
                        print(f"{spacing3}OBJECT-level comparison result is Size: COMM, Color: DIFF, AREA: DIFF, Symmetry: DIFF")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Completed OBJECT Comparisons, Analyzing the comparison results...")
                print(f"{spacing2}Searching for meaningful commonalities...")
                print(f"{spacing2}Generating a program...")
                print(f"{spacing2}Program generated!")
                print(f"{spacing2}Validating the program on this PAIR...")
                print(f"{spacing2}Program is valid on this PAIR!")
                print(f"{spacing2}Validating the program on other PAIRS...")
                print(f"{spacing2}Program is valid on NONE in {self.task.example_pair_count - 1} PAIRs -> Apply Abstraction to generalize the program")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Inter-PAIR PIXEL Analysis (T4)")
                print(f"{spacing3}Comparing {len(pair.childs[0].pixels)} PIXELs in {pair.input_grid.__repr__()} with {len(next_pair.childs[0].pixels)} PIXELs in {next_pair.input_grid.__repr__()}.")
                print(f"{spacing3}Total {len(pair.childs[0].pixels) * len(next_pair.childs[0].pixels)} pixel comparisons")
                for pix_idx_1, pix_1 in enumerate(pair.childs[0].pixels):
                    for pix_idx_2, pix_2 in enumerate(next_pair.childs[0].pixels):
                        print(f"{spacing3}Comparing PIXEL {pix_1.__repr__()} in {pair.input_grid.__repr__()} and {pix_2.__repr__()} in {next_pair.input_grid.__repr__()}.")
                        print(f"{spacing3}PIXEL-level comparison result is Color: COMM, Coordinate: DIFF")
                print()
                input("Press Enter to continue...")
                print(f"{spacing3}Comparing {len(pair.childs[1].pixels)} PIXELs in {pair.output_grid.__repr__()} with {len(next_pair.childs[1].pixels)} PIXELs in {next_pair.output_grid.__repr__()}.")
                print(f"{spacing3}Total {len(pair.childs[1].pixels) * len(next_pair.childs[1].pixels)} pixel comparisons")
                for pix_idx_1, pix_1 in enumerate(pair.childs[1].pixels):
                    for pix_idx_2, pix_2 in enumerate(next_pair.childs[1].pixels):
                        print(f"{spacing3}Comparing PIXEL {pix_1.__repr__()} in {pair.output_grid.__repr__()} and {pix_2.__repr__()} in {next_pair.output_grid.__repr__()}.")
                        print(f"{spacing3}PIXEL-level comparison result is Color: COMM, Coordinate: DIFF")
                print()
                input("Press Enter to continue...")
                print(f"{spacing2}Completed PIXEL Comparisons, Analyzing the comparison results...")
                print(f"{spacing2}Searching for meaningful commonalities...")
                print(f"{spacing2}Generating a program...")
                print(f"{spacing2}Program generated!")
                print(f"{spacing2}Validating the program on this PAIR...")
                print(f"{spacing2}Program is valid on this PAIR!")
                print(f"{spacing2}Validating the program on other PAIRS...")
                print(f"{spacing2}Program is valid on NONE in {self.task.example_pair_count - 1} PAIRs -> Apply Abstraction to generalize the program")
                print()
                input("Press Enter to continue...")

                print("----------------------------------------------------")
                print(f"With Current level of Intra-TASK Analysis, we cannot make a program that works on other PAIRs.")
                print(f"Need to inspect deeper with the comparison results to find meaningful commonalities.")
                print(f"Reveiwing all the collected comparison results...")
                print()
                input("Press Enter to continue...")
                print(f"Start Deeper Analysis of a PAIR")
                print("@@@")

                break
            else:
                pass
        print()



        # pair_program = []
        # pair_count = self.task.example_pair_count
        
        # # Collect all pair programs
        # for pair in self.task.example_pairs:
        #     pair_program.append(pair.program)
        
        # # Check if there's at least one pair with no program
        # has_empty_program = any(len(program) == 0 for program in pair_program)
        
        # # Check if there's no common program across all pairs
        # if pair_count > 0:
        #     # Find common programs across all pairs
        #     common_programs = set(pair_program[0]) if pair_program[0] else set()
        #     for program in pair_program[1:]:
        #         if program:
        #             common_programs = common_programs.intersection(set(program))
        #         else:
        #             common_programs = set()  # If any pair has no program, no common programs
        # else:
        #     common_programs = set()
        
        # has_no_common_program = len(common_programs) == 0
        
        # # Print comparison messages for all pair combinations
        # for p in range(pair_count):
        #     for pp in range(p+1, pair_count):
        #         print(f"Comparing {self.task.example_pairs[p]} and {self.task.example_pairs[pp]}")
        
        # # Check conditions and print appropriate message
        # if has_empty_program or has_no_common_program:
        #     print("    No program or No common program -> Do deeper analysis of PAIR to make program") 
        #     # T1 보다 깊게 들어가려면 Intra-PAIR Analysis를 특정 레벨 완료해야 함. 
        #     # -> 현재 가진 속성으로 만든 가설, 규칙, 프로그램은 모두 다음페어에서 동작하지 않는 것을 보이는 것이 필요. 
        # print()

        # print("Intra-PAIR Analysis (P1, P2, P3)") # Input/Output을 비교하여 다른 점 (DIFF)를 중심으로 프로그램을 만드는 것이 목표
        
        # num_pairs = self.task.example_pair_count
        # current_program = None
        # successful_program = None
        # memory = {}  # Store successful analysis results
        
        # # Main loop: Process each PAIR
        # for pair_idx in range(num_pairs):
        #     print(f"\n=== Processing PAIR {pair_idx} ===")
            
            

        






    # def temp_solve2(self):
    #     print("=== Starting Intra-TASK Analysis ===")
        
    #     # Intra-TASK Analysis
    #     task_solved = False
        
    #     while not task_solved:
    #         print("\n--- Inter-PAIR Analysis ---")
            
    #         # Check if any pair has program
    #         for pair_idx, pair in enumerate(self.task.example_pairs):
    #             print(f"Checking PAIR {pair_idx}: pair.program exists?")
                
    #             if hasattr(pair, 'program') and pair.program:
    #                 print(f"PAIR {pair_idx} has program, validating with other pairs...")
    #                 print("  Comparison T1: Inter-TASK PAIR level comparison")
    #                 print("  Comparison T2: Inter-TASK GRID level comparison") 
    #                 print("  Comparison T3: Inter-TASK OBJECT level comparison")
    #                 print("  Comparison T4: Inter-TASK PIXEL level comparison")
                    
    #                 # Validate program with all other pairs
    #                 valid_for_all = True
    #                 for other_idx, other_pair in enumerate(self.task.example_pairs):
    #                     if other_idx != pair_idx:
    #                         print(f"  Validating program on PAIR {other_idx}")
    #                         # if not validate_program(pair.program, other_pair):
    #                         #     valid_for_all = False
    #                         #     break
                    
    #                 if valid_for_all:
    #                     print("Task program found! Solver complete.")
    #                     task_solved = True
    #                     return
    #             else:
    #                 print(f"PAIR {pair_idx} has no program, entering Intra-PAIR Analysis...")
                    
    #                 # Intra-PAIR Analysis
    #                 pair_solved = False
    #                 abstraction_level = 0
                    
    #                 while not pair_solved and abstraction_level < 3:  # PIXEL, OBJECT, GRID levels
                        
    #                     if abstraction_level == 0:  # Shallow analysis
    #                         print(f"\n  === Intra-PAIR Analysis for PAIR {pair_idx} ===")
    #                         print("  Inter-GRID Analysis (shallow: color, size, symmetry)")
    #                         print("    Comparison P1: In-PAIR GRID level comparison")
                            
    #                         print("    Going deeper: Inter-OBJECT Analysis (between GRIDs)")
    #                         print("      Comparison P2: In-PAIR OBJECT level comparison - Input/Output OBJECT mapping")
                            
    #                         print("      Going deeper: Inter-PIXEL Analysis (between GRIDs)")
    #                         print("        Comparison P3: In-PAIR PIXEL level comparison - Input/Output PIXEL changes")
                            
    #                         print("        Generating fundamental level-1 program...")
    #                         # program = generate_fundamental_program()
    #                         print("        Level-1 program generated!")
                        
    #                     # Program abstraction and validation
    #                     print(f"    Program abstraction at level {abstraction_level}")
                        
    #                     if abstraction_level == 0:
    #                         print("    PIXEL level program validation")
    #                     elif abstraction_level == 1:
    #                         print("    OBJECT level program abstraction")
    #                     elif abstraction_level == 2:
    #                         print("    GRID level program abstraction")
                        
    #                     # Check with other pairs
    #                     program_works = False
    #                     for val_pair_idx, val_pair in enumerate(self.task.example_pairs):
    #                         if val_pair_idx != pair_idx:
    #                             print(f"      Validating on PAIR {val_pair_idx}...")
    #                             # if validate_program(current_program, val_pair):
    #                             #     program_works = True
                        
    #                     if program_works:
    #                         print(f"    Program works! Moving to next pair.")
    #                         pair_solved = True
    #                         break
    #                     else:
    #                         print(f"    Program failed validation.")
                            
    #                         if abstraction_level < 2:
    #                             abstraction_level += 1
    #                             print(f"    Moving to abstraction level {abstraction_level}")
    #                         else:
    #                             print("    All abstraction levels failed, entering deep analysis...")
                                
    #                             # Intra-GRID Analysis (Deep Analysis)
    #                             deep_analysis_success = False
    #                             grid_analysis_depth = 0
                                
    #                             while not deep_analysis_success and grid_analysis_depth < 2:
                                    
    #                                 if grid_analysis_depth == 0:
    #                                     print("      === Intra-GRID Analysis (Deep) ===")
    #                                     print("      Deep GRID analysis (color sets, areas, sizes)")
                                        
    #                                     for grid_idx, grid in enumerate([pair.input_grid, pair.output_grid]):
    #                                         print(f"        Analyzing GRID {grid_idx}")
    #                                         print("        Inter-OBJECT Analysis (within GRID)")
    #                                         print("          Comparison G1: In-GRID OBJECT level comparison - All objects within GRID")
                                            
    #                                         # Check if this helps
    #                                         print("        Applying deep GRID knowledge to program...")
    #                                         # enhanced_program = enhance_with_grid_knowledge()
                                            
    #                                         # Validate again
    #                                         for val_pair_idx, val_pair in enumerate(self.task.example_pairs):
    #                                             if val_pair_idx != pair_idx:
    #                                                 print(f"          Re-validating on PAIR {val_pair_idx}...")
                                            
    #                                         program_works_after_grid = False  # Simulate failure
    #                                         if program_works_after_grid:
    #                                             deep_analysis_success = True
    #                                             break
                                    
    #                                 if not deep_analysis_success and grid_analysis_depth == 0:
    #                                     print("      GRID deep analysis failed, going to OBJECT deep analysis...")
    #                                     grid_analysis_depth = 1
                                        
    #                                     print("        === Intra-OBJECT Analysis ===")
    #                                     for obj in pair.input_grid.objects:
    #                                         print(f"        Analyzing OBJECT {obj.id}")
    #                                         print("          Inter-PIXEL Analysis (within OBJECT)")
    #                                         print("            Comparison O1: In-OBJECT PIXEL level comparison - All pixels within OBJECT")
    #                                         print("            Finding relational properties...")
                                            
    #                                         # Apply object-level knowledge
    #                                         print("          Applying OBJECT relational knowledge...")
                                            
    #                                         # Validate
    #                                         for val_pair_idx, val_pair in enumerate(self.task.example_pairs):
    #                                             if val_pair_idx != pair_idx:
    #                                                 print(f"            Re-validating on PAIR {val_pair_idx}...")
                                    
    #                                 # If still no success
    #                                 if not deep_analysis_success:
    #                                     print("      Deep analysis exhausted for this pair.")
    #                                     print("      Current analysis rules cannot solve this problem.")
    #                                     return  # Stop after first pair as requested
                                
    #                             pair_solved = deep_analysis_success
                    
    #                 # After processing first pair, stop as requested
    #                 print(f"\nFirst pair processing complete. Stopping as requested.")
    #                 return

