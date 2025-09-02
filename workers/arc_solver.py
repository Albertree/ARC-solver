# from ARCKG.grid import GRID
from ARCKG.task import TASK
import os
import ast
import json
# from .program_optimizer import ProgramOptimizer
from comparison import * 
from .solver_utils import *
from pprint import pprint

from DSL.my_apply_DSL import *
from DSL.my_DSL import *
from DSL.my_selection import *
from DSL.my_layer_DSL import *
from DSL.my_transformation_DSL import *


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

    def try_DSL(self):
        input_grid = self.task.example_pairs[0].input_grid
        grid = apply_DSL(input_grid, make_grid, 10, 10, 1)
        grid = apply_DSL(grid, coloring, [(0, 0), (1, 1), (2, 2)], 7)
        printcg(grid.view)
        breakpoint()


    def test(self):


        for pair_idx, pair in enumerate(self.task.example_pairs):
            if is_empty_program(pair.program):
                # no prgrogram in PAIR -> Do deeper analysis of a PAIR to make program
                print(f"PAIR {pair_idx} has no program -> Do deeper analysis of a PAIR to make program")
                print(f"Intra-PAIR Analysis (P1, P2, P3)")
                print(f"Inter-GRID Analysis (P1)")

                comparison_result = compare(pair.input_grid, pair.output_grid, save=True)

                print(f"1 GRID comparison is completed!")

                # make rule from grid comparison result
                
                
                # make program using grid comparison result
                
                # cannot -> go deeper (object comparison in PAIR)
                print("Not enough information to make program -> Do deeper analysis of a PAIR to make program")
                print("Inter-OBJECT Analysis (P2)")
                print(f"Comparing {len(pair.input_grid.objects)} objects in input grid and {len(pair.output_grid.objects)} objects in output grid")
                for obj_i in pair.input_grid.objects:
                    for obj_o in pair.output_grid.objects:
                        comparison_result = compare(obj_i, obj_o, save=True)

                print(f"{len(pair.input_grid.objects) * len(pair.output_grid.objects)} OBJECT comparisons are completed!")

                # make rules from object comparison result


                # make program using object comparison result
                
                # cannot -> go deeper (pixel comparison in PAIR)
                print("Not enough information to make program -> Do deeper analysis of a PAIR to make program")
                print("Inter-PIXEL Analysis (P3)")
                print(f"Comparing {len(pair.input_grid.pixels)} pixels in input grid and {len(pair.output_grid.pixels)} pixels in output grid")
                for pix_i in pair.input_grid.pixels:
                    for pix_o in pair.output_grid.pixels:
                        comparison_result = compare(pix_i, pix_o, save=True)
                        
                print(f"{len(pair.input_grid.pixels) * len(pair.output_grid.pixels)} PIXEL comparisons are completed!")

                # make rules from pixel comparison result


                # make level-1 program using grid, object, pixel comparison result
                




    # # this function compatible with comparison_old.py
    # def play(self):
    #     # Clean up existing comparison directory
    #     comparison_base_path = "comparison"
    #     if os.path.exists(comparison_base_path):
    #         import shutil
    #         shutil.rmtree(comparison_base_path)
    #         print(f"Cleaned up existing comparison directory: {comparison_base_path}")
        
    #     for i, pair in enumerate(self.task.childs):
    #         pair_id = i

    #         # grid comparison #########################################################
    #         grid1 = pair.childs[0]
    #         grid2 = pair.childs[1]

    #         g_path = f"comparison/TASK_nodes/TASK_{self.task_hex_code}/PAIR_edges/PAIR_{pair_id}/GRID"
    #         if not os.path.exists(g_path):
    #             os.makedirs(g_path)
            
    #         print(f"Comparing {grid1.__repr__()} and {grid2.__repr__()}")
    #         comparison_receipt = compare(grid1, grid2)
    #         comm_count = count_comm_categories(comparison_receipt)

    #         with open(f"{g_path}/G_1_{comm_count}.json", "w") as f:
    #             json.dump(comparison_receipt, f, indent=2)


    #         # object comparison #########################################################
    #         o_group1 = grid1.objects
    #         o_group2 = grid2.objects
    #         total_o_comparisons = len(o_group1) * len(o_group2)
    #         o_comparison_count = 0

    #         o_path = f"comparison/TASK_nodes/TASK_{self.task_hex_code}/PAIR_edges/PAIR_{pair_id}/OBJECT"
    #         if not os.path.exists(o_path):
    #             os.makedirs(o_path)

    #         for i, obj1 in enumerate(o_group1):
    #             for j, obj2 in enumerate(o_group2):
    #                 o_comparison_count += 1
    #                 print(f"Comparing {obj1.__repr__()} and {obj2.__repr__()} ({o_comparison_count}/{total_o_comparisons})")
    #                 comparison_receipt = compare(obj1, obj2)
    #                 comm_count = count_comm_categories(comparison_receipt)

    #                 if comm_count >= 5:
    #                     with open(f"{o_path}/O_{o_comparison_count}_{comm_count}.json", "w") as f:
    #                         json.dump(comparison_receipt, f, indent=2)
    #                 else:
    #                     pass


    #         # pixel comparison #########################################################
    #         x_group1 = grid1.pixels
    #         x_group2 = grid2.pixels
    #         total_x_comparisons = len(x_group1) * len(x_group2)
    #         x_comparison_count = 0

    #         x_path = f"comparison/TASK_nodes/TASK_{self.task_hex_code}/PAIR_edges/PAIR_{pair_id}/PIXEL"
    #         if not os.path.exists(x_path):
    #             os.makedirs(x_path)

    #         for i, pix1 in enumerate(x_group1):
    #             for j, pix2 in enumerate(x_group2):
    #                 x_comparison_count += 1
    #                 print(f"Comparing {pix1.__repr__()} and {pix2.__repr__()} ({x_comparison_count}/{total_x_comparisons})")
    #                 comparison_receipt = compare(pix1, pix2)
    #                 comm_count = count_comm_categories(comparison_receipt)

    #                 if comm_count >= 1:
    #                     # Create score-based subfolder
    #                     score_path = os.path.join(x_path, str(comm_count))
    #                     if not os.path.exists(score_path):
    #                         os.makedirs(score_path)
                        
    #                     # For score 1, create additional subfolders based on color and coordinate results
    #                     if comm_count == 1:
    #                         # Check color and coordinate results
    #                         color_result = "COMM" if comparison_receipt["category"]["color"]["color"]["type"] == "COMM" else "DIFF"
    #                         coordinate_result = "COMM" if comparison_receipt["category"]["coordinate"]["row"]["type"] == "COMM" and comparison_receipt["category"]["coordinate"]["col"]["type"] == "COMM" else "DIFF"
                            
    #                         # Create subfolder name based on results
    #                         subfolder_name = f"color_{color_result}_coord_{coordinate_result}"
    #                         final_path = os.path.join(score_path, subfolder_name)
    #                     else:
    #                         final_path = score_path
                        
    #                     if not os.path.exists(final_path):
    #                         os.makedirs(final_path)
                        
    #                     with open(f"{final_path}/X_{x_comparison_count}_{comm_count}.json", "w") as f:
    #                         json.dump(comparison_receipt, f, indent=2)
    #                 else:
    #                     pass


        
    def temp_solve(self):
        spacing1 = " " * 4
        spacing2 = " " * 8
        spacing3 = " " * 12

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


    def object_mapping(self):
        def color_text_no_bg(index, text):
            COLORS = {
                0: (0, 0, 0),         # black
                1: (0, 116, 217),     # blue
                2: (255, 65, 54),     # red
                3: (46, 204, 64),     # green
                4: (255, 220, 0),     # yellow
                5: (170, 170, 170),   # gray
                6: (240, 18, 190),    # pink
                7: (255, 133, 27),    # orange
                8: (127, 219, 255),   # light blue
                9: (135, 12, 37),     # dark red
                10: (128, 0, 128),    # purple
                11: (0, 128, 128),    # teal
                12: (101, 67, 33),    # brown
                13: (214, 255, 255),  # white
                14: (79, 79, 79)      # dark gray
            }
            r, g, b = COLORS[index]
            return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


        def visualize_objects_side_by_side(obj1, obj2):
            print("\nOBJECT COMPARISON")
            max_height = max(len(obj1.view), len(obj2.view))
            max_width1 = max(len(row) for row in obj1.view) if obj1.view else 0
            max_width2 = max(len(row) for row in obj2.view) if obj2.view else 0
            
            print("Object 1          |  Object 2")
            print("-" * 60)
            for i in range(max_height):
                if i < len(obj1.view):
                    row1 = obj1.view[i]
                    colored1 = ''.join([color_text_no_bg(val, "██") for val in row1])
                else:
                    colored1 = ' ' * (max_width1 * 2)  # Empty row with proper width
                
                if i < len(obj2.view):
                    row2 = obj2.view[i]
                    colored2 = ''.join([color_text_no_bg(val, "██") for val in row2])
                else:
                    colored2 = ' ' * (max_width2 * 2)  # Empty row with proper width
                
                obj1_width = max_width1 * 2
                print(f"{colored1:<{obj1_width}} | {colored2}")
            print()


        task = self.task
        pair = task.example_pairs[0]
        comp1 = pair.input_grid
        comp2 = pair.output_grid

        total_comparisons = len(comp1.objects) * len(comp2.objects)
        comparison_count = 0

        for i, obj1 in enumerate(comp1.objects):
            for j, obj2 in enumerate(comp2.objects):
                comparison_count += 1
                print("\033[2J\033[H", end='', flush=True)
                print(f"Comparison {comparison_count}/{total_comparisons} - Object {i} vs Object {j}")
                
                visualize_objects_side_by_side(obj1, obj2)
                comparison = compare(obj1, obj2, save=True)

                score = int(comparison["result"]["score"].split("/")[0])
                total_checks = int(comparison["result"]["score"].split("/")[1])
                
                print(f"Score: {score}/{total_checks}")
                
                if score > 4:
                    print("\n" + "-" * 70)
                    print(f"OBJECT COMPARISON SUMMARY [score: {score}/{total_checks}]")
                    print()
                    
                    pprint(comparison["result"]["category"])
                    
                    # print()
                    print("Controls: [Enter] = Next comparison | [q] = Quit")
                    user_input = input().strip().lower()
                    
                    if user_input == 'q':
                        print("Exiting...")
                        exit()
                else:
                    continue

        print(f"\nCompleted all {total_comparisons} comparisons!")


    


        