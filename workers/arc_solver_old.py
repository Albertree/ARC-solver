# from ARCKG.grid import GRID
from ARCKG.task import TASK
import os
import ast
import json
# from .program_optimizer import ProgramOptimizer
from comparison import * 
from .solver_utils import *
from pprint import pprint
from make_rule import get_matching_actions
from program import ProgramManager

from DSL.my_apply_DSL import *
from DSL.my_DSL import *
from DSL.my_selection import *
from DSL.my_layer_DSL import *
from DSL.my_transformation_DSL import *


class ARCSolver:
    def __init__(self, task: TASK):
        self.task = task
        self.task_hex_code = task.hex_code
        self.program_manager = ProgramManager(task)
        # self.programs = []  # Store programs for each pair

    def solve(self):
        for i, pair in enumerate(self.task.example_pairs):
            print(f"Processing example pair {i} for task {self.task_hex_code}")
            lv1_program = self.program_manager.generate_level_1_program(pair, i)
            self.program_manager.save_program(lv1_program, i, "level-1")
            # lv2_program = self._generate_level_2_program(lv1_program, pair, i)
            # lv3_program = self._generate_level_3_program(lv2_program, pair, i)
        
        print(f"Level 1 programs generated for task {self.task_hex_code} in 'result_code'")
        for line in lv1_program:
            print(line)

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
                rules = get_matching_actions(comparison_result)
                pprint(rules)
                
                # Generate rule-based program using the rules
                if rules:
                    print(f"Found {len(rules)} matching rules, generating program...")
                    program = self.program_manager.generate_rule_based_program(pair, pair_idx, rules)
                    self.program_manager.save_program(program, pair_idx, "level-1")
                    print(f"Rule-based program generated and saved for pair {pair_idx}")
                else:
                    print("No matching rules found, using fallback logic...")
                    # Fallback to original level 1 program generation
                    program = self.program_manager.generate_level_1_program(pair, pair_idx)
                    self.program_manager.save_program(program, pair_idx, "level-1")
                    print(f"Fallback program generated and saved for pair {pair_idx}")
                
                # Execute the saved program
                print(f"Executing saved program for pair {pair_idx}")
                code_result = self.program_manager.execute_saved_program(pair_idx, "level-1")
                print(f"Program execution result: {code_result}")

            
                printcg(code_result.view)
                # self.validate_program()

                break
                
                # make program using grid comparison result
                
                # # cannot -> go deeper (object comparison in PAIR)
                # print("Not enough information to make program -> Do deeper analysis of a PAIR to make program")
                # print("Inter-OBJECT Analysis (P2)")
                # print(f"Comparing {len(pair.input_grid.objects)} objects in input grid and {len(pair.output_grid.objects)} objects in output grid")
                # for obj_i in pair.input_grid.objects:
                #     for obj_o in pair.output_grid.objects:
                #         comparison_result = compare(obj_i, obj_o, save=True)

                # print(f"{len(pair.input_grid.objects) * len(pair.output_grid.objects)} OBJECT comparisons are completed!")

                # # make rules from object comparison result


                # # make program using object comparison result
                
                # # cannot -> go deeper (pixel comparison in PAIR)
                # print("Not enough information to make program -> Do deeper analysis of a PAIR to make program")
                # print("Inter-PIXEL Analysis (P3)")
                # print(f"Comparing {len(pair.input_grid.objects)} objects in input grid and {len(pair.output_grid.objects)} objects in output grid")
                # for pix_i in pair.input_grid.pixels:
                #     for pix_o in pair.output_grid.pixels:
                #         comparison_result = compare(pix_i, pix_o, save=True)
                        
                # print(f"{len(pair.input_grid.pixels) * len(pair.output_grid.pixels)} PIXEL comparisons are completed!")

                # make rules from pixel comparison result


                # make level-1 program using grid, object, pixel comparison result
            

        
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


    
    
    
    # def _compare_results(self, input_grid, expected_output, generated_output, filename):
    #     """Compare expected vs generated output"""
    #     try:
    #         # Extract grid data for comparison
    #         if hasattr(generated_output, 'trimmed_grid'):
    #             generated_data = generated_output.trimmed_grid
    #         elif hasattr(generated_output, 'raw_data'):
    #             generated_data = generated_output.raw_data
    #         else:
    #             generated_data = generated_output
            
    #         expected_data = expected_output.raw_data
            
    #         # Check if sizes match
    #         if len(generated_data) != len(expected_data) or \
    #            (len(generated_data) > 0 and len(generated_data[0]) != len(expected_data[0])):
    #             print(f"❌ Size mismatch: Expected {len(expected_data)}x{len(expected_data[0]) if expected_data else 0}, "
    #                   f"Got {len(generated_data)}x{len(generated_data[0]) if generated_data else 0}")
    #             return
            
    #         # Check if contents match
    #         matches = 0
    #         total_cells = len(expected_data) * len(expected_data[0])
            
    #         for r in range(len(expected_data)):
    #             for c in range(len(expected_data[0])):
    #                 if r < len(generated_data) and c < len(generated_data[0]):
    #                     if generated_data[r][c] == expected_data[r][c]:
    #                         matches += 1
            
    #         accuracy = (matches / total_cells) * 100 if total_cells > 0 else 0
            
    #         if accuracy == 100:
    #             print(f"✅ Perfect match! Accuracy: {accuracy:.1f}%")
    #         elif accuracy >= 80:
    #             print(f"🟡 Good match! Accuracy: {accuracy:.1f}%")
    #         else:
    #             print(f"❌ Poor match! Accuracy: {accuracy:.1f}%")
            
    #         # Show grid comparison if accuracy is not perfect
    #         if accuracy < 100:
    #             from basics.utils import printcg
    #             print("Grid comparison:")
    #             printcg([input_grid.raw_data, expected_data, generated_data], 
    #                    titles=["Input", "Expected", "Generated"])
                
    #     except Exception as e:
    #         print(f"❌ Comparison error: {e}")



        