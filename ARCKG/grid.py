from .ARCKG_component import ARCKGComponent
from DSL.dsl3 import find_all_objects
from .grid_component import GridComponent
from .pixel import PIXEL, PIXELInfo
from .object import OBJECT, OBJECTInfo
from typing import NamedTuple


class GRIDInfo(NamedTuple):
    id: int
    type: str
    raw_data: list[list[int]]

class GRID(GridComponent) :
    def __init__(self, id:int, type:str, parent:ARCKGComponent, raw_data:list): #, object_list:list[OBJECT]=[], pixel_list:list[PIXEL]=[], raw_data:list[list[int]]=[[1,0],[0,1]]) :
        super().__init__(id, type, parent)
        self.raw_data = raw_data
        self.pixels = []
        self.objects = []
        self.property = dict()


    def colorgrid_to_colcoord(self, colorgrid):
        return [(colorgrid[i][j], (i, j)) for i in range(len(colorgrid)) for j in range(len(colorgrid[0])) if colorgrid[i][j] != 13]

    def colcoord_to_coordinate(self, colcoord):
        return [(colcoord[i][1][0], colcoord[i][1][1]) for i in range(len(colcoord))]

    def grid_color(self, grid):
        return sorted(list(set([grid[i][j] for i in range(len(grid)) for j in range(len(grid[0])) if grid[i][j] != 13])))

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

    def margin_of_grid(self):
        margin = []
        for i in range(len(self.raw_data)):
            for j in range(len(self.raw_data[0])):
                if i == 0 or i == len(self.raw_data) - 1 or j == 0 or j == len(self.raw_data[0]) - 1:
                    margin.append((i, j))
        return margin

    def inner_of_grid(self):
        inner = []  
        for i in range(len(self.raw_data)):
            for j in range(len(self.raw_data[0])):
                if i != 0 and i != len(self.raw_data) - 1 and j != 0 and j != len(self.raw_data[0]) - 1:
                    inner.append((i, j))
        return inner

    def corner_of_grid(self):
        corner = []
        for i in range(len(self.raw_data)):
            for j in range(len(self.raw_data[0])):
                if (i == 0 or i == len(self.raw_data) - 1) and (j == 0 or j == len(self.raw_data[0]) - 1):
                    corner.append((i, j))
        return corner

    def edge_of_grid(self):
        edge = []
        for i in range(len(self.raw_data)):
            for j in range(len(self.raw_data[0])):
                if i == 0 or i == len(self.raw_data) - 1 or j == 0 or j == len(self.raw_data[0]) - 1:
                    if not ((i == 0 or i == len(self.raw_data) - 1) and (j == 0 or j == len(self.raw_data[0]) - 1)):
                        edge.append((i, j))
        return edge

    def center_of_grid(self):
        center = []
        if len(self.raw_data) % 2 == 1:
            # vertical odd, horizontal odd
            if len(self.raw_data[0]) % 2 == 1:
                center.append((len(self.raw_data) // 2, len(self.raw_data[0]) // 2))
            # vertical odd, horizontal even
            else:
                center.append((len(self.raw_data) // 2, len(self.raw_data[0]) // 2 - 1))
                center.append((len(self.raw_data) // 2, len(self.raw_data[0]) // 2))
        else:
            # vertical even, horizontal odd
            if len(self.raw_data[0]) % 2 == 1:
                center.append((len(self.raw_data) // 2 - 1, len(self.raw_data[0]) // 2))
                center.append((len(self.raw_data) // 2, len(self.raw_data[0]) // 2))
            # vertical even, horizontal even
            else:
                center.append((len(self.raw_data) // 2 - 1, len(self.raw_data[0]) // 2 - 1))
                center.append((len(self.raw_data) // 2 - 1, len(self.raw_data[0]) // 2))
                center.append((len(self.raw_data) // 2, len(self.raw_data[0]) // 2 - 1))
                center.append((len(self.raw_data) // 2, len(self.raw_data[0]) // 2))
        return center

    def grid_horizontal_symmetry(self):
        # Check if the grid is horizontally symmetric
        rows = len(self.raw_data)
        cols = len(self.raw_data[0])
        for i in range(rows // 2 + 1):
            if self.raw_data[i] != self.raw_data[rows - i - 1]:
                return False
        return True

    def grid_vertical_symmetry(self):
        # Check if the grid is vertically symmetric
        rows = len(self.raw_data)
        cols = len(self.raw_data[0])
        for j in range(cols // 2 + 1):
            for i in range(rows):
                if self.raw_data[i][j] != self.raw_data[i][cols - j - 1]:
                    return False
        return True

    def grid_diagonal_symmetry(self):
        # Check if the grid is symmetric along the main diagonal
        size = len(self.raw_data)
        for i in range(size):
            for j in range(i + 1, size):
                if self.raw_data[i][j] != self.raw_data[j][i]:
                    return False
        return True

    def grid_antidiagonal_symmetry(self):
        # Check if the grid is symmetric along the anti-diagonal
        size = len(self.raw_data)
        for i in range(size):
            for j in range(size - i - 1):
                if self.raw_data[i][j] != self.raw_data[size - j - 1][size - i - 1]:
                    return False
        return True
    
    def update_childs(self):
        # Your implementation here
        pass
    
    def get_most_frequent_color(self):
        colors = {}
        for r in range(self.height):
            for c in range(self.width):
                color = self.raw_data[r][c]
                if color in colors:
                    colors[color] += 1
                else:
                    colors[color] = 1
        return max(colors, key=colors.get)

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
        self.property['color'] = {color: True for color in self.color}
        self.property['color'].update({'color_count': len(self.color)})

        # area
        self.property['area'] = {color: sum(1 for row in self.colorgrid for cell in row if cell == color) for color in self.color}
        self.property['area'].update({'total': sum(self.property['area'].values())})

        # symmetry
        self.property['symmetry'] = {
            'hori_symm': self.hori_symm,
            'verti_symm': self.verti_symm,
            'diag_symm': self.diag_symm,
            'anti_symm': self.anti_symm
        }

        # breakpoint()


    @staticmethod
    def from_json(grid_info:GRIDInfo, parent:ARCKGComponent):
        ggg = GRID(id=grid_info.id, type=grid_info.type, raw_data=grid_info.raw_data, parent=parent)

        pixel_list = []
        for r in range(len(grid_info.raw_data)):
            for c in range(len(grid_info.raw_data[0])):
                pixel_info = PIXELInfo(
                    id = r * len(grid_info.raw_data[0]) + c,
                    type = 'pixel',
                    raw_data = [(grid_info.raw_data[r][c], (r,c))] 
                )
                xxx = PIXEL.from_json(pixel_info, parent=ggg)
                pixel_list.append(xxx)
            ggg.pixels = pixel_list
        
        object_list = []
        objects_raw = find_all_objects(grid_info.raw_data)
        for i, obj in enumerate(objects_raw):
            object_info = OBJECTInfo(
                id = i, 
                type = 'object', 
                raw_data = obj
            )
            ooo = OBJECT.from_json(object_info, parent=ggg)
            object_list.append(ooo)
        ggg.objects = object_list
    
        ggg.update_property()
        ggg.to_json()
        return ggg
    
    def to_json(self):
        import os
        import json

        grid_dict = self.property
        path = f'memory/task_{self.parent[0].parent.id}/pair_{self.parent[0].id}/grid_{self.id}/'
        file_name = f'grid_{self.id}.json'
        if not os.path.exists(path):
            os.makedirs(path)
        
        with open(f'{path}/{file_name}', 'w') as f:
            json.dump(grid_dict, f, indent=2)

    def __repr__(self):
        grid_type = "input" if self.id==0 else "output"
        pair_id = self.parent[0].id
        task_id = self.parent[0].parent.hex_code
        return f"GRID({grid_type} grid of PAIR({pair_id}th pair of TASK({task_id})))"
        