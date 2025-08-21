import os
import importlib.util
from ..basics.utils import printcg
from ..managers.task_manager import TASKManager
from ..ARCKG.grid import GRID
from ..DSL.apply_DSL import apply_DSL
from ..DSL.transformation_DSL import coloring, make_grid

def main(task_hex_code_filter=None):
    base_result_dir = os.path.join(os.path.dirname(__file__), "..", "result_code")
    
    tasks_to_validate = [d for d in os.listdir(base_result_dir) if os.path.isdir(os.path.join(base_result_dir, d))]
    if task_hex_code_filter:
        tasks_to_validate = [task_hex_code_filter]

    for task_hex in tasks_to_validate:
        task_dir = os.path.join(base_result_dir, task_hex)
        for level_dir in sorted(os.listdir(task_dir)):
            level_path = os.path.join(task_dir, level_dir)
            if os.path.isdir(level_path) and "level" in level_dir:
                for filename in sorted(os.listdir(level_path)):
                    if filename.endswith(".py"):
                        parts = filename.replace(".py", "").split("_")
                        pair_number = int(parts[1])
                        
                        task_manager = TASKManager.from_hex_code(task_hex)
                        pair = task_manager.example_pairs[pair_number]
                        
                        module_name = f"solver.result_code.{task_hex}.{level_dir}.{filename.replace('.py', '')}"
                        spec = importlib.util.spec_from_file_location(module_name, os.path.join(level_path, filename))
                        module = importlib.util.module_from_spec(spec)
                        
                        # Helper for level-3's coordinate_of function
                        def coordinate_of(object_name):
                            obj_id = int(object_name.split("_")[1])
                            for obj in pair.input_grid.objects:
                                if obj.id == obj_id:
                                    return obj.coordinate
                            return []

                        module.apply_DSL = apply_DSL
                        module.coloring = coloring
                        module.make_grid = make_grid
                        module.coordinate_of = coordinate_of
                        
                        spec.loader.exec_module(module)
                        
                        input_grid_obj = GRID(id=0, type='input', parent=pair, raw_data=pair.input_grid.raw_data)
                        input_grid_obj.update_property()
                        input_grid_obj.update_childs()

                        generated_output_grid_obj = module.solve(input_grid_obj)
                        generated_output_grid = generated_output_grid_obj.trimmed_grid

                        print(f"--- File: {task_hex}/{level_dir}/{filename} ---")
                        printcg([pair.input_grid.raw_data, pair.output_grid.raw_data, generated_output_grid], 
                                titles=["Input", "Expected Output", "Generated Output"])

if __name__ == "__main__":
    main() 