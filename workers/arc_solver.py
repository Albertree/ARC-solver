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
                print(f"Intra-PAIR Analysis (P1, P2, P3)")
                print(f"Inter-GRID Analysis (P1)")

                comparison_result = compare(pair.input_grid, pair.output_grid, save=True)

                print(f"1 GRID comparison is completed!")

                # make rule from grid comparison result
                rules = get_matching_actions(comparison_result)
                pprint(rules)
                print("^^^ above is selected matching rules ^^^")
                breakpoint()
                
                # make program using grid comparison result
                if rules:
                    program = self.program_manager.generate_program_with_rules(pair, pair_idx, rules)
                    self.program_manager.save_program(program, pair_idx, "GRID")
                    print(f"Rule-based program generated and saved for pair {pair_idx}")

                    pprint(program)
                    print("^^^ above is program ^^^")
                    breakpoint()
                    
                    # Execute the saved program
                    print(f"Executing saved program for pair {pair_idx}")
                    code_result = self.program_manager.execute_saved_program(pair_idx, "GRID")

                    printcg(code_result.view)
                    print("^^^ above is code_result ^^^")
                    breakpoint()


                    if code_result.view == pair.output_grid.view:
                        print(f"^^^ program can solve the PAIR {pair_idx} ^^^")
                    else:
                        print(f"^^^ program cannot even solve the current PAIR -> need deeper analysis in OBJECT level^^^")
                    breakpoint()


                    comparison_result = compare(code_result, pair.output_grid, save=False)
                    path = id_pair_to_comparison_path(get_component_full_id(code_result), get_component_full_id(pair.output_grid))
                    path = f"{self.task_hex_code}_PAIR_{pair_idx}-GRID-level_TFG{pair_idx}.json"
                    
                    save_comparison_result(comparison_result, path)
                    print("^^^ above is comparison result of code_result and output_grid ^^^")
                    breakpoint()

                else:
                    print("No matching rules found, using fallback logic...")

                
                # cannot -> go deeper (object comparison in PAIR)
                print("Not enough information to make program -> Do deeper analysis of a PAIR to make program")
                print("Inter-OBJECT Analysis (P2)")
                print(f"Comparing {len(pair.input_grid.objects)} objects in input grid and {len(pair.output_grid.objects)} objects in output grid")
                for obj_i in pair.input_grid.objects:
                    for obj_o in pair.output_grid.objects:
                        comparison_result = compare(obj_i, obj_o, save=True)

                print(f"{len(pair.input_grid.objects) * len(pair.output_grid.objects)} OBJECT comparisons are completed!")

                # make rules from object comparison result

                breakpoint()


                # make program using object comparison result
                
                # cannot -> go deeper (pixel comparison in PAIR)
                print("Not enough information to make program -> Do deeper analysis of a PAIR to make program")
                print("Inter-PIXEL Analysis (P3)")
                print(f"Comparing {len(pair.input_grid.objects)} objects in input grid and {len(pair.output_grid.objects)} objects in output grid")
                for pix_i in pair.input_grid.pixels:
                    for pix_o in pair.output_grid.pixels:
                        comparison_result = compare(pix_i, pix_o, save=True)
                        
                print(f"{len(pair.input_grid.pixels) * len(pair.output_grid.pixels)} PIXEL comparisons are completed!")

                # make rules from pixel comparison result

                breakpoint()


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
                printcg(result.view)
            else:
                print(f"Failed to execute program for pair {pair_idx}")

    def object_mapping(self):
        def color_text_no_bg(index, text):
            colors = [
                '\033[91m',  # Red
                '\033[92m',  # Green
                '\033[93m',  # Yellow
                '\033[94m',  # Blue
                '\033[95m',  # Magenta
                '\033[96m',  # Cyan
                '\033[97m',  # White
            ]
            reset = '\033[0m'
            color = colors[index % len(colors)]
            return f"{color}{text}{reset}"

        def visualize_objects_side_by_side(obj1, obj2):
            print("=" * 60)
            print(f"{color_text_no_bg(0, 'Object 1')} vs {color_text_no_bg(1, 'Object 2')}")
            print("=" * 60)
            
            # Print object 1
            print(f"{color_text_no_bg(0, 'Object 1:')}")
            printcg(obj1.view)
            print()

            # Print object 2
            print(f"{color_text_no_bg(1, 'Object 2:')}")
            printcg(obj2.view)
            print()
            
            # Print comparison
            print(f"{color_text_no_bg(2, 'Comparison:')}")
            if obj1.raw_data == obj2.raw_data:
                print(f"{color_text_no_bg(2, '✓ Objects are identical')}")
            else:
                print(f"{color_text_no_bg(2, '✗ Objects are different')}")
            print("=" * 60)

        # Example usage
        if self.task.example_pairs:
            pair = self.task.example_pairs[0]
            input_grid = pair.input_grid
            output_grid = pair.output_grid
            
            # Extract objects from grids (this would need to be implemented based on your object extraction logic)
            # For now, just show the grids
            print("Input Grid:")
            printcg(input_grid.view)
            print("\nOutput Grid:")
            printcg(output_grid.view)
