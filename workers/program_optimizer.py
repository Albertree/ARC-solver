import ast
from collections import defaultdict

class ProgramOptimizer:
    def __init__(self, program_code, input_grid=None):
        self.original_code = program_code
        self.input_grid = input_grid
        self.tree = ast.parse(self.original_code)
        self.solve_func = self.tree.body[0]
        self.make_grid_line = None
        self.coloring_calls = []
        self._parse_program()

    def _parse_program(self):
        """Extracts make_grid and coloring calls from the program."""
        coloring_ops = []
        for node in self.solve_func.body:
            if not isinstance(node, ast.Assign):
                continue

            call_node = node.value
            if not isinstance(call_node, ast.Call) or not isinstance(call_node.func, ast.Name):
                continue

            if call_node.func.id == 'apply_DSL':
                args = call_node.args
                if len(args) > 1 and isinstance(args[1], ast.Name):
                    dsl_func_name = args[1].id
                    if dsl_func_name == 'make_grid':
                        self.make_grid_line = node
                    elif dsl_func_name == 'coloring':
                        coords_node = args[2]
                        color_node = args[3]
                        
                        coords = ast.literal_eval(coords_node)
                        color = ast.literal_eval(color_node)
                        
                        # Store the original nodes for later reconstruction
                        coloring_ops.append({
                            'coords_node': coords_node,
                            'color_node': color_node,
                            'coords': coords,
                            'color': color
                        })
        self.coloring_calls = coloring_ops

    def _rebuild_program(self, new_coloring_groups):
        """Reconstructs the program with a new set of coloring calls."""
        new_body = [self.solve_func.body[0]]  # tfg0 = input_grid
        
        current_grid_var_idx = 0
        if self.make_grid_line:
            new_body.append(self.make_grid_line)
            current_grid_var_idx = 1
        
        for group in new_coloring_groups:
            prev_grid_var = f"tfg{current_grid_var_idx}"
            current_grid_var_idx += 1
            current_grid_var = f"tfg{current_grid_var_idx}"
            
            coords_str = str(group['coords'])
            color_str = str(group['color'])

            new_line = f"{current_grid_var} = apply_DSL({prev_grid_var}, coloring, {coords_str}, {color_str})"
            new_body.append(ast.parse(new_line).body[0])

        final_var = f"tfg{current_grid_var_idx}"
        new_body.append(ast.parse(f"output_grid = {final_var}").body[0])
        new_body.append(ast.Return(value=ast.Name(id='output_grid', ctx=ast.Load())))

        self.solve_func.body = new_body
        return ast.unparse(self.solve_func)
        
    def optimize_by_color(self):
        """Groups all coloring operations by color."""
        color_groups = defaultdict(list)
        for op in self.coloring_calls:
            for coord in op['coords']:
                color_groups[op['color']].append(tuple(coord))
        
        new_groups = [{'coords': coords, 'color': color} for color, coords in color_groups.items()]
        return self._rebuild_program(new_groups)

    def optimize_by_row(self):
        """Groups coloring operations by row and color."""
        row_groups = defaultdict(list)
        for op in self.coloring_calls:
            for coord in op['coords']:
                row_groups[(coord[0], op['color'])].append(tuple(coord))
        
        new_groups = [{'coords': coords, 'color': key[1]} for key, coords in row_groups.items()]
        return self._rebuild_program(new_groups)

    def optimize_by_column(self):
        """Groups coloring operations by column and color."""
        col_groups = defaultdict(list)
        for op in self.coloring_calls:
            for coord in op['coords']:
                col_groups[(coord[1], op['color'])].append(tuple(coord))
            
        new_groups = [{'coords': coords, 'color': key[1]} for key, coords in col_groups.items()]
        return self._rebuild_program(new_groups)

    def optimize_with_objects(self, optimized_code):
        """Replaces coordinate lists with object references if they match."""
        if not self.input_grid:
            return optimized_code # Cannot perform this optimization without the grid

        tree = ast.parse(optimized_code)
        solve_func = tree.body[0]
        
        object_coord_map = {f"object_{obj.id}": set(obj.coordinate) for obj in self.input_grid.objects}

        for node in ast.walk(solve_func):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'apply_DSL':
                args = node.args
                if len(args) > 1 and isinstance(args[1], ast.Name) and args[1].id == 'coloring':
                    coords_node = args[2]
                    try:
                        coords_list = ast.literal_eval(coords_node)
                        coords_set = {tuple(c) for c in coords_list}
                        
                        for obj_name, obj_coords in object_coord_map.items():
                            if coords_set == obj_coords:
                                # Replace the list of coordinates with a call to coordinate_of
                                new_call = ast.Call(
                                    func=ast.Name(id='coordinate_of', ctx=ast.Load()),
                                    args=[ast.Constant(value=obj_name)],
                                    keywords=[]
                                )
                                args[2] = new_call
                                break
                    except (ValueError, TypeError):
                        # Node is not a simple list of coordinates, so skip it
                        continue
        
        return ast.unparse(tree) 