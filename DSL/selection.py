from DSL.transformation_DSL import pprint

# SELECTION
def selection_to_colorgrid(selection, main_grid):
    # non_selected = [coord for coord in main_grid.coordinate if coord not in selection]
    
    # # colorgrid = main_grid.colorgrid
    colorgrid = [[13 for _ in range(len(main_grid.colorgrid[0]))] for _ in range(len(main_grid.colorgrid))]
    # for coord in non_selected:  
    #     colorgrid[coord[0]][coord[1]] = 13

    for coord in selection:
        colorgrid[coord[0]][coord[1]] = main_grid.colorgrid[coord[0]][coord[1]]
    return colorgrid

def colorgrid_to_colcoord(colorgrid):
    return [(colorgrid[i][j], (i, j)) for i in range(len(colorgrid)) for j in range(len(colorgrid[0]))]# if colorgrid[i][j] != 13]

def get_key_points(selection):
    center = []
    min_row = 30
    max_row = 0
    min_col = 30
    max_col = 0
    for coord in selection: 
        if coord[0] < min_row:
            min_row = coord[0]
        if coord[0] > max_row:
            max_row = coord[0]
        if coord[1] < min_col:
            min_col = coord[1]
        if coord[1] > max_col:
            max_col = coord[1]

    if (max_col - min_col) % 2 == 0: # horizontal length is odd
        if (max_row - min_row) % 2 == 0: #vertical length is odd
            center.append((min_row + ((max_row - min_row) // 2), min_col + ((max_col - min_col) // 2)))
        else:
            center.append((min_row + ((max_row - min_row) // 2), min_col + ((max_col - min_col) // 2)))
            center.append((min_row + ((max_row - min_row) // 2), min_col + ((max_col - min_col) // 2) + 1))
    else:
        if (max_row - min_row) % 2 == 0:
            center.append((min_row + ((max_row - min_row) // 2), min_col + ((max_col - min_col) // 2)))
            center.append((min_row + ((max_row - min_row) // 2), min_col + ((max_col - min_col) // 2) + 1))
        else:
            center.append((min_row + ((max_row - min_row) // 2), min_col + ((max_col - min_col) // 2)))
            center.append((min_row + ((max_row - min_row) // 2), min_col + ((max_col - min_col) // 2) + 1))
            center.append((min_row + ((max_row - min_row) // 2) + 1, min_col + ((max_col - min_col) // 2)))
            center.append((min_row + ((max_row - min_row) // 2) + 1, min_col + ((max_col - min_col) // 2) + 1))

    # center, left_top, left_bottom, right_bottom, right_top
    return center, (min_row, min_col), (max_row, min_col), (max_row, max_col), (min_row, max_col)
            
def get_bbox(colorgrid, left_top, right_bottom):
    return [row[left_top[1]:right_bottom[1]+1] for row in colorgrid[left_top[0]:right_bottom[0]+1]]

def get_bbox_coordinate(bbox, bbox_pos):
    return [(bbox_pos[0] + i, bbox_pos[1] + j) for i in range(len(bbox)) for j in range(len(bbox[0]))]

def get_bbox_colcoord(bbox, bbox_pos):
    return [(bbox[i][j], (bbox_pos[0] + i, bbox_pos[1] + j)) for i in range(len(bbox)) for j in range(len(bbox[0]))]

class SELECTION:
    def __init__(self, selection, main_grid): # selection is a list of coordinates, main_grid is a GRID object
        self.id = (None, None, None, None, None)
        self.type = "selection"
        self.repr = selection

        # coordinate = list of coordinates
        self.coordinate = selection
        # colorgrid = 2d array of colors same size as main_grid, and 13 for non-selected, original color for selected
        self.colorgrid = selection_to_colorgrid(selection, main_grid)
        # colcoord = list of colcoords translated from colorgrid
        self.colcoord = colorgrid_to_colcoord(self.colorgrid)

        self.center = get_key_points(selection)[0]
        self.left_top = get_key_points(selection)[1]
        self.left_bottom = get_key_points(selection)[2]
        self.right_bottom = get_key_points(selection)[3]
        self.right_top = get_key_points(selection)[4]

        # bbox = 2d array of colors, subgrid of colorgrid
        self.bbox = get_bbox(self.colorgrid, self.left_top, self.right_bottom)
        # bbox_pos = position of the bbox in the main_grid
        self.bbox_pos = self.left_top
        # bbox_coordinate = list of coordinates in the bbox
        self.bbox_coordinate = get_bbox_coordinate(self.bbox, self.bbox_pos)
        # bbox_colcoord = list of colcoords in the bbox
        self.bbox_colcoord = get_bbox_colcoord(self.bbox, self.bbox_pos)
        
        # width = width of the selection bbox
        self.width = len(self.bbox[0])
        # height = height of the selection bbox
        self.height = len(self.bbox)
        # size = (width, height) of the selection bbox
        self.size = (self.width, self.height)
        # shape = shape of the selection
        self.shape = None
        # area = area of the selection
        self.area = None


        self.view = None