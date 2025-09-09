from typing import NamedTuple
from .ARCKG_component import ARCKGComponent
from .grid_component import GridComponent
from .pixel import PIXEL
from .types.type import PIXELData_Type

class OBJECTInfo(NamedTuple):
    id: int
    type: str
    raw_data: frozenset

class OBJECT(GridComponent):
    def __init__(self, id:int, type:str, parent:ARCKGComponent, raw_data:frozenset): #, pixel_data:PIXELData_Type):
        super().__init__(id, type, parent)
        self.raw_data = raw_data
        self.property = dict()

    def object_colcoord_to_colorgrid(self, object):
        object = list(object)

        max_col = 0
        max_row = 0
        min_col = 100
        min_row = 100
        for n in range(len(object)):
            if object[n][1][0] > max_col:
                max_col = object[n][1][0]
            if object[n][1][1] > max_row:
                max_row = object[n][1][1] 

            if object[n][1][0] < min_col:
                min_col = object[n][1][0]
            if object[n][1][1] < min_row:
                min_row = object[n][1][1]

        if min_col == 100:
            min_col = max_col
        if min_row == 100:
            min_row = max_row
        
        if min_col == 0:
            col_move = 0
        else:
            col_move = min_col

        if min_row == 0:
            row_move = 0
        else:
            row_move = min_row

        colorgrid = [[13 for j in range(max_row - min_row + 1)] for i in range(max_col - min_col + 1)]
        for n in range(len(object)):
            colorgrid[object[n][1][0]-(col_move)][object[n][1][1]-(row_move)] = object[n][0]
        return colorgrid

    def colcoord_to_coordinate(self, colcoord):
        return [(colcoord[i][1][0], colcoord[i][1][1]) for i in range(len(colcoord))]


    def measure_shape(self, object):
        # return an array of 0 or 1, 0 for value 13, 1 for other values
        shape = [[0 for j in range(len(object[0]))] for i in range(len(object))]
        for i in range(len(object)):
            for j in range(len(object[0])): 
                if object[i][j] != 13:
                    shape[i][j] = 1 # 0 for valid color (color between 0 and 9)
                else:
                    shape[i][j] = -1 # -1 for no color (color 13)
        return shape
    
    def measure_area(self, shape):
        return sum([1 for i in range(len(shape)) for j in range(len(shape[0])) if shape[i][j] == 1])

    def absolute_coordinate_of_object(self, coordinate, pos):
        return [(coordinate[i][0] + pos[0], coordinate[i][1] + pos[1]) for i in range(len(coordinate))]

    def center_of_grid(self, grid):
        center = []
        if len(grid) % 2 == 1:
            # vertical odd, horizontal odd
            if len(grid[0]) % 2 == 1:
                center.append((len(grid) // 2, len(grid[0]) // 2))
            # vertical odd, horizontal even
            else:
                center.append((len(grid) // 2, len(grid[0]) // 2 - 1))
                center.append((len(grid) // 2, len(grid[0]) // 2))
        else:
            # vertical even, horizontal odd
            if len(grid[0]) % 2 == 1:
                center.append((len(grid) // 2 - 1, len(grid[0]) // 2))
                center.append((len(grid) // 2, len(grid[0]) // 2))
            # vertical even, horizontal even
            else:
                center.append((len(grid) // 2 - 1, len(grid[0]) // 2 - 1))
                center.append((len(grid) // 2 - 1, len(grid[0]) // 2))
                center.append((len(grid) // 2, len(grid[0]) // 2 - 1))
                center.append((len(grid) // 2, len(grid[0]) // 2))
        return center

    def margin_of_grid(self, grid):
        margin = []
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if i == 0 or i == len(grid) - 1 or j == 0 or j == len(grid[0]) - 1:
                    margin.append((i, j))
        return margin

    def inner_of_grid(self, grid):
        inner = []  
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if i != 0 and i != len(grid) - 1 and j != 0 and j != len(grid[0]) - 1:
                    inner.append((i, j))
        return inner

    def corner_of_grid(self, grid):
        corner = []
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if (i == 0 or i == len(grid) - 1) and (j == 0 or j == len(grid[0]) - 1):
                    corner.append((i, j))
        return corner

    def edge_of_grid(self, grid):
        edge = []
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if i == 0 or i == len(grid) - 1 or j == 0 or j == len(grid[0]) - 1:
                    if not ((i == 0 or i == len(grid) - 1) and (j == 0 or j == len(grid[0]) - 1)):
                        edge.append((i, j))
        return edge

    def grid_horizontal_symmetry(self, grid):
        # Check if the grid is horizontally symmetric
        rows = len(grid)
        cols = len(grid[0])
        for i in range(rows // 2 + 1):
            if grid[i] != grid[rows - i - 1]:
                return False
        return True

    def grid_vertical_symmetry(self, grid):
        # Check if the grid is vertically symmetric
        rows = len(grid)
        cols = len(grid[0])
        for j in range(cols // 2 + 1):
            for i in range(rows):
                if grid[i][j] != grid[i][cols - j - 1]:
                    return False
        return True

    def grid_diagonal_symmetry(self, grid):
        # Check if the grid is symmetric along the main diagonal
        size = len(grid)
        for i in range(size):
            for j in range(i + 1, size):
                if grid[i][j] != grid[j][i]:
                    return False
        return True

    def grid_antidiagonal_symmetry(self, grid):
        # Check if the grid is symmetric along the anti-diagonal
        size = len(grid)
        for i in range(size):
            for j in range(size - i - 1):
                if grid[i][j] != grid[size - j - 1][size - i - 1]:
                    return False
        return True
    
    def update_property(self, object):
        self.childs = self.pixels

        self.colorgrid = self.object_colcoord_to_colorgrid(object['obj']) 
        self.colcoord = list(object['obj'])
        
        self.view = self.colorgrid

        self.pos = object["pos"]
        self.color = object["color"]
        self.method = object["method"]
        self.coordinate = self.colcoord_to_coordinate(self.colcoord)

        self.height = len(self.colorgrid)
        self.width = len(self.colorgrid[0])
        self.size = (self.height, self.width)
        self.shape = self.measure_shape(self.colorgrid)
        self.area = self.measure_area(self.shape)
        self.center = self.absolute_coordinate_of_object(self.center_of_grid(self.colorgrid), self.pos)

        self.margin = self.absolute_coordinate_of_object(self.margin_of_grid(self.colorgrid), self.pos)
        self.inner = self.absolute_coordinate_of_object(self.inner_of_grid(self.colorgrid), self.pos)
        self.corner = self.absolute_coordinate_of_object(self.corner_of_grid(self.colorgrid), self.pos)
        self.edge = self.absolute_coordinate_of_object(self.edge_of_grid(self.colorgrid), self.pos)

        self.left_top = (self.pos[0], self.pos[1])
        self.right_top = (self.pos[0], self.pos[1] + self.width - 1)
        self.left_bottom = (self.pos[0] + self.height - 1, self.pos[1])
        self.right_bottom = (self.pos[0] + self.height - 1, self.pos[1] + self.width - 1)

        self.hori_symm = self.grid_horizontal_symmetry(self.colorgrid) # 상하 대칭
        self.verti_symm = self.grid_vertical_symmetry(self.colorgrid) # 좌우 대칭
        if self.height == self.width:
            self.diag_symm = self.grid_diagonal_symmetry(self.colorgrid)
            self.anti_symm = self.grid_antidiagonal_symmetry(self.colorgrid)
        else:
            self.diag_symm = False
            self.anti_symm = False


        self.property['color'] = self.color
        self.property['coordinate'] = self.coordinate
        
        self.property['pos'] = {
            'left_top': {
                'row_index': self.pos[0],
                'col_index': self.pos[1]
            },
            'right_top': {
                'row_index': self.pos[0],
                'col_index': self.pos[1] + self.width - 1
            },
            'left_bottom': {
                'row_index': self.pos[0] + self.height - 1,
                'col_index': self.pos[1]
            },
            'right_bottom': {
                'row_index': self.pos[0] + self.height - 1,
                'col_index': self.pos[1] + self.width - 1
            }
        }
        self.property['method'] = self.method

        self.property['size'] = {
            'height': self.height,
            'width': self.width
        }

        self.property['shape'] = self.shape

        self.property['area'] = self.area

        # self.property['center'] = self.center

        self.property['symmetry'] = {
            'hori_symm': self.hori_symm,
            'verti_symm': self.verti_symm,
            'diag_symm': self.diag_symm,
            'anti_symm': self.anti_symm
        }

    
    @staticmethod
    def from_json(object_info:OBJECTInfo, parent:ARCKGComponent):
        ooo = OBJECT(id=object_info.id, type=object_info.type, raw_data=object_info.raw_data, parent=parent)
        obj_coordinate = ooo.colcoord_to_coordinate(list(object_info.raw_data['obj']))

        pixel_list = []
        for pixel in parent.pixels:
            if pixel.coordinate in obj_coordinate:
                pixel_list.append(pixel)
                pixel.parent.append(ooo)
                pixel.to_json()
        ooo.pixels = pixel_list
        ooo.update_property(object_info.raw_data)
        ooo.to_json()    
        
        return ooo

    def to_json(self):
        import os
        import json

        object_dict = self.property
        object_path = f'memory/TASK_nodes/TASK_{self.parent[0].parent[0].parent.hex_code}/'
        object_path += f'PAIR_nodes/PAIR_{self.parent[0].parent[0].id}/'
        object_path += f'GRID_nodes/{self.parent[-1].type.upper()}_{self.parent[-1].id}/'
        object_path += f'OBJECT_nodes/OBJECT_{self.id}/'
        if not os.path.exists(object_path):
            os.makedirs(object_path)

        # OBJECT_node - OBJECT_property
        path = f'{object_path}/OBJECT_property'
        file_name = f'OBJECT_{self.id}_property.json'
        if not os.path.exists(path):
            os.makedirs(path)
        
        with open(f'{path}/{file_name}', 'w') as f:
            json.dump(object_dict, f, indent=2)

        # OBJECT_edge
        object_edge_path = f'memory/TASK_nodes/TASK_{self.parent[0].parent[0].parent.hex_code}/'
        object_edge_path += f'PAIR_nodes/PAIR_{self.parent[0].parent[0].id}/'
        object_edge_path += f'GRID_nodes/{self.parent[-1].type.upper()}_{self.parent[-1].id}/'
        object_edge_path += f'OBJECT_edges'
        if not os.path.exists(object_edge_path):
            os.makedirs(object_edge_path)
        
        # Update integrated ARCKG JSON
        # self.update_integrated_arckg_json()
    
    def update_integrated_arckg_json(self):
        """Update the integrated ARCKG JSON with object information"""
        import os
        import json
        
        arckg_file = f'memory/TASK_nodes/ARCKG_{self.parent[0].parent[0].parent.hex_code}.json'
        
        # Check if integrated ARCKG file exists
        if not os.path.exists(arckg_file):
            return
        
        try:
            with open(arckg_file, 'r') as f:
                integrated_arckg = json.load(f)
            
            # Find the pair, grid, and object data
            pair_id_str = f"({self.parent[0].parent[0].parent.hex_code}, {self.parent[0].parent[0].id}, None, None, None, 'pair')"
            grid_id_str = f"('{self.parent[0].parent[0].parent.hex_code}', {self.parent[0].parent[0].id}, {self.parent[0].id}, None, None, 'grid')"
            object_id_str = f"('{self.parent[0].parent[0].parent.hex_code}', {self.parent[0].parent[0].id}, {self.parent[0].id}, {self.id}, None, 'object')"
            
            # Find the pair
            if str(self.parent[0].parent[0].id) in integrated_arckg["PAIR_nodes"]:
                pair_data = integrated_arckg["PAIR_nodes"][str(self.parent[0].parent[0].id)]
                if pair_data["id"] == pair_id_str:
                    # Find the grid
                    if str(self.parent[0].id) in pair_data["GRID_nodes"]:
                        grid_data = pair_data["GRID_nodes"][str(self.parent[0].id)]
                        if grid_data["id"] == grid_id_str:
                            # Check if object already exists
                            object_exists = False
                            if str(self.id) in grid_data["OBJECT_nodes"]:
                                obj_data = grid_data["OBJECT_nodes"][str(self.id)]
                                if obj_data["id"] == object_id_str:
                                    # Update existing object
                                    obj_data["property"] = self.property
                                    object_exists = True
                            
                            # If object doesn't exist, add it
                            if not object_exists:
                                obj_data = {
                                    "id": object_id_str,
                                    "type": "OBJECT",
                                    "data": {},
                                    "property": self.property,
                                    "PIXEL_edges": {},
                                    "PIXEL_nodes": {}
                                }
                                grid_data["OBJECT_nodes"][str(self.id)] = obj_data
            
            # Save updated integrated ARCKG JSON
            with open(arckg_file, 'w') as f:
                json.dump(integrated_arckg, f, indent=2)
                
        except Exception as e:
            print(f"Error updating integrated ARCKG JSON: {e}")

    def __repr__(self):
        color_str = ', '.join([str(c) for c in self.color if self.color[c] == True])
        return f"OBJECT(Size {self.height}x{self.width} and color {color_str} {self.type}, at {self.pos}, in {self.parent})"