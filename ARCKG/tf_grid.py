from .grid import GRID, GRIDInfo
from DSL.my_layer_DSL import merge_layers
from typing import NamedTuple
from .ARCKG_component import ARCKGComponent
from .pixel import PIXEL, PIXELInfo
from .object import OBJECT, OBJECTInfo
from DSL.my_DSL import find_all_objects

class TF_GRIDInfo(NamedTuple):
    id: int
    type: str
    raw_data: list[list[int]]

class TF_GRID(GRID):
    # 정적 카운터 - TF_GRID가 생성될 때마다 증가
    _id_counter = -1
    
    @classmethod
    def get_next_id(cls):
        """새로운 TF_GRID ID를 반환하고 카운터를 증가시킵니다."""
        cls._id_counter += 1
        return cls._id_counter
    
    @classmethod
    def reset_id_counter(cls):
        """TF_GRID ID 카운터를 초기화합니다."""
        cls._id_counter = -1
    
    def __init__(self, id: int, type: str,  raw_data: list[list[int]], accumulated_layers: list[list[int]], parent: ARCKGComponent):
        self.accumulated_layers = accumulated_layers
        self.merged_grid = merge_layers(self.accumulated_layers)
        self.trimmed_grid = raw_data
        
        super().__init__(id=id, type="tfgrid", parent=parent[0], raw_data=self.trimmed_grid)
        self.pixels = []
        self.objects = []

    @staticmethod
    def make_trimmed_grid(merged_grid, mask):
        max_row = 0
        max_col = 0
        for i in range(len(mask)):
            for j in range(len(mask[0])):
                if mask[i][j] == 13:
                    max_row = i
                    max_col = j

        trimmed_grid = [[13 for _ in range(30, max_col + 1)] for _ in range(30, max_row + 1)]

        for i in range(len(trimmed_grid)):
            for j in range(len(trimmed_grid[0])):
                trimmed_grid[i][j] = merged_grid[30 + i][30 + j]
        
        return trimmed_grid 
    
    def update_property(self):
        self.childs = self.pixels + self.objects
        self.pixels = self.pixels
        self.objects = self.objects

        self.view = self.raw_data

        self.colorgrid = self.raw_data
        self.colcoord = self.colorgrid_to_colcoord(self.colorgrid)

        self.color = self.grid_color(self.colorgrid)
        self.coordinate = self.colcoord_to_coordinate(self.colcoord)

        self.height = len(self.colorgrid)
        self.width = len(self.colorgrid[0])
        self.size = (self.height, self.width)
        self.shape = self.measure_shape(self.colorgrid)
        self.area = self.measure_area(self.shape)
        self.center = self.center_of_grid()

        self.margin = self.margin_of_grid()
        self.inner = self.inner_of_grid()
        self.corner = self.corner_of_grid()
        self.edge = self.edge_of_grid()

        self.left_top = (0, 0)
        self.right_top = (0, self.width)
        self.left_bottom = (self.height, 0)
        self.right_bottom = (self.height, self.width)

        self.hori_symm = self.grid_horizontal_symmetry()
        self.verti_symm = self.grid_vertical_symmetry()
        if self.height == self.width:
            self.diag_symm = self.grid_diagonal_symmetry()
            self.anti_symm = self.grid_antidiagonal_symmetry()
        else:
            self.diag_symm = False
            self.anti_symm = False



        # size
        self.property['size'] = {
            'height': self.height,
            'width': self.width
        }

        # color
        # self.property['color'] = {color: True for color in self.color}
        # self.property['color'].update({'color_count': len(self.color)})
        self.property['color'] = self.color

        # area
        self.property['area'] = {int(color): sum(1 for row in self.colorgrid for cell in row if cell == int(color)) for color in self.color}
        self.property['area'].update({'total': sum(self.property['area'].values())})

        # symmetry
        self.property['symmetry'] = {
            'hori_symm': self.hori_symm,
            'verti_symm': self.verti_symm,
            'diag_symm': self.diag_symm,
            'anti_symm': self.anti_symm
        }


    @staticmethod
    def from_json(tfgrid_info:TF_GRIDInfo, accumulated_layers:list[list[int]], parent:ARCKGComponent):
        tfggg = TF_GRID(id=tfgrid_info.id, type=tfgrid_info.type, raw_data=tfgrid_info.raw_data, accumulated_layers=accumulated_layers, parent=parent)

        pixel_list = []
        for r in range(len(tfgrid_info.raw_data)):
            for c in range(len(tfgrid_info.raw_data[0])):
                pixel_info = PIXELInfo(
                    id = r * len(tfgrid_info.raw_data[0]) + c,
                    type = 'pixel',
                    raw_data = [(tfgrid_info.raw_data[r][c], (r,c))] 
                )
                xxx = PIXEL.from_json(pixel_info, parent=tfggg)
                pixel_list.append(xxx)
            tfggg.pixels = pixel_list
        
        object_list = []
        objects_raw = find_all_objects(tfgrid_info.raw_data)
        for i, obj in enumerate(objects_raw):
            object_info = OBJECTInfo(
                id = i, 
                type = 'object', 
                raw_data = obj
            )
            ooo = OBJECT.from_json(object_info, parent=tfggg)
            object_list.append(ooo)
        tfggg.objects = object_list
    
        tfggg.update_property()
        tfggg.to_json()
        return tfggg

    
    def to_json(self):
        import os
        import json

        grid_dict = self.property
        grid_path = f'memory/TASK_nodes/TASK_{self.parent[0].parent.hex_code}/PAIR_nodes/PAIR_{self.parent[0].id}/TFGRID_nodes/TFGRID_{self.id}/'
        if not os.path.exists(grid_path):
            os.makedirs(grid_path)

        # GRID_property (same structure as GRID folders)
        path = f'{grid_path}/GRID_property'
        file_name = f'GRID_{self.id}_property.json'
        if not os.path.exists(path):
            os.makedirs(path)

        with open(f'{path}/{file_name}', 'w') as f:
            json.dump(grid_dict, f, indent=2)

        # GRID_edges (same structure as GRID folders)
        grid_edge_path = f'memory/TASK_nodes/TASK_{self.parent[0].parent.hex_code}/'
        grid_edge_path += f'PAIR_nodes/PAIR_{self.parent[0].id}/'
        grid_edge_path += f'TFGRID_edges'
        if not os.path.exists(grid_edge_path):
            os.makedirs(grid_edge_path)

        # Create OBJECT_nodes and OBJECT_edges folders (same structure as GRID)
        object_nodes_path = f'{grid_path}/OBJECT_nodes'
        object_edges_path = f'{grid_path}/OBJECT_edges'
        if not os.path.exists(object_nodes_path):
            os.makedirs(object_nodes_path)
        if not os.path.exists(object_edges_path):
            os.makedirs(object_edges_path)
            # Create hierarchical subfolders in OBJECT_edges
            os.makedirs(f'{object_edges_path}/OBJECT', exist_ok=True)
            os.makedirs(f'{object_edges_path}/PIXEL', exist_ok=True)

        # Create PIXEL_nodes and PIXEL_edges folders (same structure as GRID)
        pixel_nodes_path = f'{grid_path}/PIXEL_nodes'
        pixel_edges_path = f'{grid_path}/PIXEL_edges'
        if not os.path.exists(pixel_nodes_path):
            os.makedirs(pixel_nodes_path)
        if not os.path.exists(pixel_edges_path):
            os.makedirs(pixel_edges_path)
            # Create hierarchical subfolders in PIXEL_edges
            os.makedirs(f'{pixel_edges_path}/PIXEL', exist_ok=True)

        # Save objects and pixels if they exist
        if hasattr(self, 'objects') and self.objects:
            for obj in self.objects:
                obj.to_json()
        
        if hasattr(self, 'pixels') and self.pixels:
            for pixel in self.pixels:
                pixel.to_json()
        
        # Update integrated ARCKG JSON
        # self.update_integrated_arckg_json()


    def __repr__(self):
        return f"TF_GRID(id={self.id}, type={self.type}, parent={self.parent}, raw_data={self.raw_data})"