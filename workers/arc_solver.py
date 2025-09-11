# from ARCKG.grid import GRID
from managers.arc_manager import ARCManager
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
from basics.utils import printcg


class ARCSolver:
    def __init__(self, task_hex_code: str):
        self.task = ARCManager.from_hex_code(task_hex_code)
        self.task_hex_code = task_hex_code
        self.program_manager = ProgramManager()
        # self.programs = []  # Store programs for each pair

    def solve(self):
        for i, pair in enumerate(self.task.example_pairs):
            print(f"Processing example pair {i} for task {self.task_hex_code}")
            lv1_program = self.program_manager.generate_program(pair, i)
            self.program_manager.save_program(lv1_program, i, "GRID", self.task_hex_code)
            # lv2_program = self._generate_level_2_program(lv1_program, pair, i)
            # lv3_program = self._generate_level_3_program(lv2_program, pair, i)
        
        print(f"Level 1 programs generated for task {self.task_hex_code} in 'result_code'")
        if lv1_program:
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

                # ==================== GRID LEVEL ====================
                print(f"\n=== GRID Level Program Generation ===")
                comparison_result = compare(pair.input_grid, pair.output_grid, save=True)
                rules = get_matching_actions(comparison_result)
                
                # Generate GRID program
                if rules:
                    grid_program = self.program_manager.generate_program_with_rules(pair, pair_idx, rules)
                    self.program_manager.save_program(grid_program, pair_idx, "GRID", self.task_hex_code)
                    print(f"✅ GRID program generated with {len(rules)} rules")
                else:
                    # Create a basic GRID program with wrapper structure
                    grid_program = self.program_manager.generate_program_with_rules(pair, pair_idx, [])
                    self.program_manager.save_program(grid_program, pair_idx, "GRID", self.task_hex_code)
                    print(f"⚠️ No GRID rules found, created basic program")

                # Execute GRID program to get result for OBJECT level
                print(f"\n=== GRID Level Program Execution ===")
                grid_result = self.program_manager.execute_saved_program(pair_idx, "GRID", self.task_hex_code)
                
                if grid_result:
                    print("GRID Program Result:")
                    printcg(grid_result.view)
                    print("\nExpected Output:")
                    printcg(pair.output_grid.view)
                    
                    if grid_result.view == pair.output_grid.view:
                        print(f"✅ GRID program successfully solves PAIR {pair_idx}!")
                        continue  # Success! Move to next pair
                    else:
                        print(f"❌ GRID program cannot solve PAIR {pair_idx} -> proceeding to OBJECT level")
                else:
                    print(f"❌ Failed to execute GRID program for PAIR {pair_idx}")
                    grid_result = pair.input_grid



                    # comparison_result = compare(code_result, pair.output_grid, save=False)
                    # path = id_pair_to_comparison_path(get_component_full_id(code_result), get_component_full_id(pair.output_grid))
                    # path = f"{self.task_hex_code}_PAIR_{pair_idx}-GRID-level_TFG{pair_idx}.json"
                    
                    # save_comparison_result(comparison_result, path)
                    # print("^^^ above is comparison result of code_result and output_grid ^^^")
                    # breakpoint()

                # breakpoint()  # Commented out to allow OBJECT generation to proceed





                # ==================== OBJECT LEVEL ====================
                print(f"\n=== OBJECT Level Program Generation ===")
                print(f"Comparing {len(grid_result.objects)} objects in GRID result and {len(pair.output_grid.objects)} objects in output grid")
                
                # Accumulate all actions from all object comparisons
                all_object_actions = []
                for obj_i in grid_result.objects:
                    for obj_o in pair.output_grid.objects:
                        comparison_result = compare(obj_i, obj_o, save=True)
                        rules = get_matching_actions(comparison_result)
    
                        if rules:
                            all_object_actions.extend(rules)
                
                # Generate OBJECT program starting from GRID program
                if all_object_actions:
                    print(f"Found {len(all_object_actions)} total object actions, generating OBJECT program...")
                    # Start with GRID program and add OBJECT actions
                    object_program = self.program_manager.generate_program_with_rules(pair, pair_idx, all_object_actions, base_program=grid_program)
                    self.program_manager.save_program(object_program, pair_idx, "OBJECT", self.task_hex_code)
                else:
                    # No OBJECT actions found, use GRID program as OBJECT program
                    print(f"⚠️ No OBJECT rules found, using GRID program as OBJECT program")
                    self.program_manager.save_program(grid_program, pair_idx, "OBJECT", self.task_hex_code)

                # Execute OBJECT program to get result for PIXEL level
                print(f"\n=== OBJECT Level Program Execution ===")
                object_result = self.program_manager.execute_saved_program(pair_idx, "OBJECT", self.task_hex_code)
                
                if object_result:
                    print("OBJECT Program Result:")
                    printcg(object_result.view)
                    print("\nExpected Output:")
                    printcg(pair.output_grid.view)
                    
                    if object_result.view == pair.output_grid.view:
                        print(f"✅ OBJECT program successfully solves PAIR {pair_idx}!")
                        continue  # Success! Move to next pair
                    else:
                        print(f"❌ OBJECT program cannot solve PAIR {pair_idx} -> proceeding to PIXEL level")
                else:
                    print(f"❌ Failed to execute OBJECT program for PAIR {pair_idx}")
                    object_result = grid_result


                # print(f"{len(pair.input_grid.objects) * len(pair.output_grid.objects)} OBJECT comparisons are completed!")

                # make rules from object comparison result

                # breakpoint()  # Commented out to allow PIXEL generation to proceed


                # make program using object comparison result
                








                # ==================== PIXEL LEVEL ====================
                print(f"\n=== PIXEL Level Program Generation ===")
                print(f"Comparing {len(object_result.pixels)} pixels in OBJECT result and {len(pair.output_grid.pixels)} pixels in output grid")
                
                # Debug: Check object_result properties
                print(f"OBJECT result grid size: {object_result.height}x{object_result.width}")
                print(f"OBJECT result colorgrid size: {len(object_result.colorgrid)}x{len(object_result.colorgrid[0]) if object_result.colorgrid else 'N/A'}")
                print(f"Output grid size: {pair.output_grid.height}x{pair.output_grid.width}")
                print(f"Output grid colorgrid size: {len(pair.output_grid.colorgrid)}x{len(pair.output_grid.colorgrid[0]) if pair.output_grid.colorgrid else 'N/A'}")
                
                # Accumulate all actions from all pixel comparisons
                all_pixel_actions = []
                for pix_i in object_result.pixels:
                    for pix_o in pair.output_grid.pixels:
                        comparison_result = compare(pix_i, pix_o, save=True)
                        rules = get_matching_actions(comparison_result)
                
                        if rules:
                            all_pixel_actions.extend(rules)
                
                # Generate PIXEL program starting from OBJECT program
                if all_pixel_actions:
                    print(f"Found {len(all_pixel_actions)} total pixel actions, generating PIXEL program...")
                    # Get the OBJECT program to use as base
                    object_program = self.program_manager.load_program(pair_idx, "OBJECT", self.task_hex_code)
                    if object_program:
                        object_program_lines = object_program.split('\n')
                    else:
                        object_program_lines = grid_program
                    # Start with OBJECT program and add PIXEL actions
                    pixel_program = self.program_manager.generate_program_with_rules(pair, pair_idx, all_pixel_actions, base_program=object_program_lines)
                    self.program_manager.save_program(pixel_program, pair_idx, "PIXEL", self.task_hex_code)
                else:
                    # No PIXEL actions found, use OBJECT program as PIXEL program
                    print(f"⚠️ No PIXEL rules found, using OBJECT program as PIXEL program")
                    object_program = self.program_manager.load_program(pair_idx, "OBJECT", self.task_hex_code)
                    if object_program:
                        object_program_lines = object_program.split('\n')
                        self.program_manager.save_program(object_program_lines, pair_idx, "PIXEL", self.task_hex_code)
                    else:
                        self.program_manager.save_program(grid_program, pair_idx, "PIXEL", self.task_hex_code)

                # Execute and verify PIXEL level program
                print(f"\n=== PIXEL Level Program Execution ===")
                try:
                    code_result = self.program_manager.execute_saved_program(pair_idx, "PIXEL", self.task_hex_code)
                    
                    if code_result:
                        print("PIXEL Program Result:")
                        printcg(code_result.view)
                        print("\nExpected Output:")
                        printcg(pair.output_grid.view)
                        
                        if code_result.view == pair.output_grid.view:
                            print(f"✅ PIXEL program successfully solves PAIR {pair_idx}!")
                        else:
                            print(f"❌ PIXEL program cannot solve PAIR {pair_idx}")
                    else:
                        print(f"❌ Failed to execute PIXEL program for PAIR {pair_idx}")
                except Exception as e:
                    print(f"❌ PIXEL program execution failed for PAIR {pair_idx}: {e}")
                    print("Continuing to next pair...")


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


if __name__ == "__main__":
    solver = ARCSolver("007bbfb7")
    solver.test()
