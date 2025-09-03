from .ARCKG_component import ARCKGComponent
from .grid_component import GridComponent
from typing import NamedTuple
from .types.type import PIXELData_Type

class PIXELInfo(NamedTuple):
    id: int
    type: str
    raw_data: PIXELData_Type

class PIXEL(GridComponent):
    def __init__(self, id:int, type:str, parent:list, raw_data:PIXELData_Type): #, pixel_data:PIXELData_Type):
        super().__init__(id, type, parent)
        self.raw_data = raw_data
        self.property = dict()

    def update_property(self, pixel):
        self.colorgrid = [[pixel[0]]]
        self.colcoord = [pixel]
        
        self.color = pixel[0][0]
        self.coordinate = pixel[0][1]
        self.row_index = pixel[0][1][0]
        self.col_index = pixel[0][1][1]

        self.view = [[self.color]]

        # self.property['colorgrid'] = self.colorgrid
        # self.property['colcoord'] = self.colcoord
        # self.property['view'] = self.view
        self.property['color'] = self.color
        self.property['coordinate'] = {
            'row_index': self.row_index,
            'col_index': self.col_index
        }

    @staticmethod
    def from_json(pixel_info:PIXELInfo, parent:ARCKGComponent):
        xxx = PIXEL(id=pixel_info.id, type=pixel_info.type, raw_data=pixel_info.raw_data, parent=parent)
        xxx.update_property(pixel_info.raw_data)
        xxx.to_json()
        return xxx

    def to_json(self):
        import os
        import json

        pixel_dict = self.property
        pixel_path = f'memory/TASK_nodes/TASK_{self.parent[0].parent[0].parent.hex_code}/'
        pixel_path += f'PAIR_nodes/PAIR_{self.parent[0].parent[0].id}/'
        pixel_path += f'GRID_nodes/GRID_{self.parent[0].id}/'
    
        # PIXEL_node - PIXEL_property
        file_name = f'PIXEL_{self.id}_property.json'
        
        # Save under grid (always save under grid)
        grid = self.parent[0] if self.parent else None
        if grid and hasattr(grid, 'parent') and grid.parent:
            pair = grid.parent[0] if isinstance(grid.parent, list) else grid.parent
            if pair and hasattr(pair, 'parent') and pair.parent:
                task = pair.parent
                if task:
                    path_g = f'{pixel_path}/PIXEL_nodes/PIXEL_{self.id}/PIXEL_property'
                    if not os.path.exists(path_g):
                        os.makedirs(path_g)
                    with open(f'{path_g}/{file_name}', 'w') as f:
                        json.dump(pixel_dict, f, indent=2)
                    
                    # PIXEL_edge (if activated, PIXEL_edges will be saved under GRID_nodes/GRID_N/)
                    pixel_g_edge_path = f'memory/TASK_nodes/TASK_{task.hex_code}/'
                    pixel_g_edge_path += f'PAIR_nodes/PAIR_{pair.id}/'
                    pixel_g_edge_path += f'GRID_nodes/GRID_{grid.id}/'
                    pixel_g_edge_path += f'PIXEL_edges'
                    if not os.path.exists(pixel_g_edge_path):
                        os.makedirs(pixel_g_edge_path)
        
        # Save under object parents if they exist
        for parent in self.parent:
            if hasattr(parent, 'type') and parent.type == 'object':
                obj_grid = parent.parent[0] if hasattr(parent, 'parent') and parent.parent else None
                if obj_grid and hasattr(obj_grid, 'parent') and obj_grid.parent:
                    obj_pair = obj_grid.parent[0] if isinstance(obj_grid.parent, list) else obj_grid.parent
                    if obj_pair and hasattr(obj_pair, 'parent') and obj_pair.parent:
                        obj_task = obj_pair.parent
                        if obj_task:
                            path_o = f'{pixel_path}/OBJECT_nodes/OBJECT_{self.parent[1].id}/PIXEL_nodes/PIXEL_{self.id}/PIXEL_property'
                            if not os.path.exists(path_o):
                                os.makedirs(path_o)
                            with open(f'{path_o}/{file_name}', 'w') as f:
                                json.dump(pixel_dict, f, indent=2)

                            # PIXEL_edge
                            pixel_o_edge_path = f'memory/TASK_nodes/TASK_{obj_task.hex_code}/'
                            pixel_o_edge_path += f'PAIR_nodes/PAIR_{obj_pair.id}/'
                            pixel_o_edge_path += f'GRID_nodes/GRID_{obj_grid.id}/'
                            pixel_o_edge_path += f'OBJECT_nodes/OBJECT_{parent.id}/'
                            pixel_o_edge_path += f'PIXEL_edges'
                            if not os.path.exists(pixel_o_edge_path):
                                os.makedirs(pixel_o_edge_path)
        
        # Update integrated ARCKG JSON
        # self.update_integrated_arckg_json()
    
    def update_integrated_arckg_json(self):
        """Update the integrated ARCKG JSON with pixel information"""
        import os
        import json
        
        # Get task hex code from parent hierarchy
        grid = self.parent[0] if self.parent else None
        if not grid or not hasattr(grid, 'parent') or not grid.parent:
            return
            
        pair = grid.parent[0] if isinstance(grid.parent, list) else grid.parent
        if not pair or not hasattr(pair, 'parent') or not pair.parent:
            return
            
        task = pair.parent
        if not task:
            return
            
        arckg_file = f'memory/TASK_nodes/ARCKG_{task.hex_code}.json'
        
        # Check if integrated ARCKG file exists
        if not os.path.exists(arckg_file):
            return
        
        try:
            with open(arckg_file, 'r') as f:
                integrated_arckg = json.load(f)
            
            # Find the pair, grid, and pixel data
            pair_id_str = f"({task.hex_code}, {pair.id}, None, None, None, 'pair')"
            grid_id_str = f"('{task.hex_code}', {pair.id}, {grid.id}, None, None, 'grid')"
            
            # Find the pair
            if str(pair.id) in integrated_arckg["PAIR_nodes"]:
                pair_data = integrated_arckg["PAIR_nodes"][str(pair.id)]
                if pair_data["id"] == pair_id_str:
                    # Find the grid
                    if str(grid.id) in pair_data["GRID_nodes"]:
                        grid_data = pair_data["GRID_nodes"][str(grid.id)]
                        if grid_data["id"] == grid_id_str:
                            # Add pixel to grid's PIXEL_nodes
                            pixel_id_str = f"('{task.hex_code}', {pair.id}, {grid.id}, None, {self.id}, 'pixel')"
                            
                            # Check if pixel already exists
                            pixel_exists = False
                            if str(self.id) in grid_data["PIXEL_nodes"]:
                                pixel_data = grid_data["PIXEL_nodes"][str(self.id)]
                                if pixel_data["id"] == pixel_id_str:
                                    # Update existing pixel
                                    pixel_data["property"] = self.property
                                    pixel_exists = True
                            
                            # If pixel doesn't exist in grid, add it
                            if not pixel_exists:
                                pixel_data = {
                                    "id": pixel_id_str,
                                    "type": "PIXEL",
                                    "data": {},
                                    "property": self.property
                                }
                                grid_data["PIXEL_nodes"][str(self.id)] = pixel_data
                            
                            # Also add pixel to object if it exists
                            if hasattr(grid, 'objects') and grid.objects:
                                for obj in grid.objects:
                                    if hasattr(obj, 'pixels') and obj.pixels and self in obj.pixels:
                                        if str(obj.id) in grid_data["OBJECT_nodes"]:
                                            obj_data = grid_data["OBJECT_nodes"][str(obj.id)]
                                            obj_pixel_id_str = f"('{task.hex_code}', {pair.id}, {grid.id}, {obj.id}, {self.id}, 'pixel')"
                                            
                                            # Check if pixel already exists in object
                                            obj_pixel_exists = False
                                            if str(self.id) in obj_data["PIXEL_nodes"]:
                                                obj_pixel_data = obj_data["PIXEL_nodes"][str(self.id)]
                                                if obj_pixel_data["id"] == obj_pixel_id_str:
                                                    # Update existing pixel
                                                    obj_pixel_data["property"] = self.property
                                                    obj_pixel_exists = True
                                            
                                            # If pixel doesn't exist in object, add it
                                            if not obj_pixel_exists:
                                                obj_pixel_data = {
                                                    "id": obj_pixel_id_str,
                                                    "type": "PIXEL",
                                                    "data": {},
                                                    "property": self.property
                                                }
                                                obj_data["PIXEL_nodes"][str(self.id)] = obj_pixel_data
            
            # Save updated integrated ARCKG JSON
            with open(arckg_file, 'w') as f:
                json.dump(integrated_arckg, f, indent=2)
                
        except Exception as e:
            print(f"Error updating integrated ARCKG JSON: {e}")

    def __repr__(self):
        return f"PIXEL({self.color}, {self.coordinate})"