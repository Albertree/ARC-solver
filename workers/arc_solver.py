# from ARCKG.grid import GRID
from ARCKG.task import TASK
import os
import ast
import json
# from .program_optimizer import ProgramOptimizer
from comparison import * 
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
            lv1_program = self.program_manager.generate_program(pair, i)
            self.program_manager.save_program(lv1_program, i, "GRID")
            # lv2_program = self._generate_level_2_program(lv1_program, pair, i)
            # lv3_program = self._generate_level_3_program(lv2_program, pair, i)
        
        print(f"Level 1 programs generated for task {self.task_hex_code} in 'result_code'")
        for line in lv1_program:
            print(line)

    # def try_DSL(self):
    #     input_grid = self.task.example_pairs[0].input_grid
    #     grid = apply_DSL(input_grid, make_grid, 10, 10, 1)
    #     grid = apply_DSL(grid, coloring, [(0, 0), (1, 1), (2, 2)], 7)
    #     printcg(grid.view)
    #     breakpoint()

    def test(self):
        for pair_idx, pair in enumerate(self.task.example_pairs):
            if len(pair.program) == 0:
                # no prgrogram in PAIR -> Do deeper analysis of a PAIR to make program
                print(f"PAIR {pair_idx} has no program -> Do deeper analysis of a PAIR to make program")

                comparison_result = compare(pair.input_grid, pair.output_grid, save=True)
                rules = get_matching_actions(comparison_result)
                
                # make program using grid comparison result
                if rules:
                    program = self.program_manager.generate_program_with_rules(pair, pair_idx, rules)
                    self.program_manager.save_program(program, pair_idx, "GRID")                   

                    # code_result = self.program_manager.execute_saved_program(pair_idx, "GRID")
                    # printcg(code_result.view)

                    # if code_result.view == pair.output_grid.view:
                    #     print(f"^^^ program can solve the PAIR {pair_idx} ^^^")
                    # else:
                    #     print(f"^^^ program cannot even solve the current PAIR -> need deeper analysis in OBJECT level^^^")
                    # breakpoint()



                    # comparison_result = compare(code_result, pair.output_grid, save=False)
                    # path = id_pair_to_comparison_path(get_component_full_id(code_result), get_component_full_id(pair.output_grid))
                    # path = f"{self.task_hex_code}_PAIR_{pair_idx}-GRID-level_TFG{pair_idx}.json"
                    
                    # save_comparison_result(comparison_result, path)
                    # print("^^^ above is comparison result of code_result and output_grid ^^^")
                    # breakpoint()

                breakpoint()  # Commented out to allow OBJECT generation to proceed





                # cannot -> go deeper (object comparison in PAIR)
                print("Not enough information to make program -> Do deeper analysis of a PAIR to make program")
                print("Inter-OBJECT Analysis (P2)")
                print(f"Comparing {len(pair.input_grid.objects)} objects in input grid and {len(pair.output_grid.objects)} objects in output grid")
                
                # Accumulate all actions from all object comparisons
                all_object_actions = []
                for obj_i in pair.input_grid.objects:
                    for obj_o in pair.output_grid.objects:
                        comparison_result = compare(obj_i, obj_o, save=True)
                        rules = get_matching_actions(comparison_result)
    
                        if rules:
                            all_object_actions.extend(rules)
                
                # Generate program with all accumulated actions
                if all_object_actions:
                    print(f"Found {len(all_object_actions)} total object actions, generating program...")
                    program = self.program_manager.generate_program_with_rules(pair, pair_idx, all_object_actions)
                    self.program_manager.save_program(program, pair_idx, "OBJECT")

                    # code_result = self.program_manager.execute_saved_program(pair_idx, "OBJECT")
                    # printcg(code_result.view)


                # print(f"{len(pair.input_grid.objects) * len(pair.output_grid.objects)} OBJECT comparisons are completed!")

                # make rules from object comparison result

                breakpoint()  # Commented out to allow PIXEL generation to proceed


                # make program using object comparison result
                








                # cannot -> go deeper (pixel comparison in PAIR)
                print("Not enough information to make program -> Do deeper analysis of a PAIR to make program")
                print("Inter-PIXEL Analysis (P3)")
                print(f"Comparing {len(pair.input_grid.pixels)} pixels in input grid and {len(pair.output_grid.pixels)} pixels in output grid")
                
                # Accumulate all actions from all pixel comparisons
                all_pixel_actions = []
                for pix_i in pair.input_grid.pixels:
                    for pix_o in pair.output_grid.pixels:
                        comparison_result = compare(pix_i, pix_o, save=True)
                        rules = get_matching_actions(comparison_result)
                
                        if rules:
                            all_pixel_actions.extend(rules)
                
                # Generate program with all accumulated actions
                if all_pixel_actions:
                    print(f"Found {len(all_pixel_actions)} total pixel actions, generating program...")
                    program = self.program_manager.generate_program_with_rules(pair, pair_idx, all_pixel_actions)
                    self.program_manager.save_program(program, pair_idx, "PIXEL")

                    # code_result = self.program_manager.execute_saved_program(pair_idx, "PIXEL")
                    # printcg(code_result.view)


                # print(f"{len(pair.input_grid.pixels) * len(pair.output_grid.pixels)} PIXEL comparisons are completed!")

                # make rules from pixel comparison result

                # breakpoint()  # Commented out to allow full execution


                # make GRID level program using grid, object, pixel comparison result
            

        



    def temp_solve(self):
        """Temporary solve method for testing"""
        for pair_idx, pair in enumerate(self.task.example_pairs):
            print(f"Processing pair {pair_idx}")
            
            # Generate and save program
            program = self.program_manager.generate_and_save_program(pair, pair_idx, level="GRID")
            
            # Execute the program
            result = self.program_manager.execute_saved_program(pair_idx, "GRID")
            
            if result:
                print(f"Pair {pair_idx} result:")
                # printcg(result.view)
            else:
                print(f"Failed to execute program for pair {pair_idx}")






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
