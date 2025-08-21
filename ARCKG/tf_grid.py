from .grid import GRID
from DSL.layer_utils import merge_layers

class TF_GRID(GRID):
    def __init__(self, accumulated_layers, t, p, g):
        self.accumulated_layers = accumulated_layers
        self.merged_grid = merge_layers(accumulated_layers)
        self.trimmed_grid = self.make_trimmed_grid(self.merged_grid, accumulated_layers[-1])
        super().__init__(id=t, type="tf_grid", parent=p, raw_data=self.trimmed_grid)
        self.update_childs()
        self.view = self.trimmed_grid

    def make_trimmed_grid(self, merged_grid, mask):
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