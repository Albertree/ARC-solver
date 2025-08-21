import json
import numpy as np
import matplotlib.pyplot as plt
# from .ARCLOADER import *

settings = json.load(open('./basics/settings.json', 'r'))
colors_rgb = settings['colors_rgb']

# color note 
# {
# "colors_rgb": [
#     [0, 0, 0], // 0: black
#     [0, 116, 217], // 1: blue
#     [255, 65, 54], // 2: red
#     [46, 204, 64], // 3: green
#     [255, 220, 0], // 4: yellow
#     [170, 170, 170], // 5: gray
#     [240, 18, 190], // 6: pink
#     [255, 133, 27], // 7: orange
#     [127, 219, 255], // 8: light blue
#     [135, 12, 37], // 9: dark red
#     [128, 0, 128], // 10: purple (difference grid)
#     [0, 128, 128], // 11: teal (SELECTION)
#     [101, 67, 33], // 12: brown (edit space)
#     [214, 255, 255] // 13: white (transparent)
#     [79, 79, 79] // 14: black (mask for view)
# ]
# }

def _plot_grid(ax, grid_data, color='#AAB7B8', alpha=1.0, linewidth=1.5):
    """Helper function to plot a single grid on a given matplotlib axis."""
    ax.grid(True, which='both', color=color, alpha=alpha, linewidth=linewidth)
    ax.xaxis.set_ticks_position('top')
    ax.set_xticks([x - 0.5 for x in range(1 + np.array(grid_data).shape[1])])
    ax.yaxis.set_ticks_position('left')
    ax.set_yticks([x - 0.5 for x in range(1 + np.array(grid_data).shape[0])])
    ax.tick_params(top=False, labeltop=False, left=False, labelleft=False)
    ax.imshow(grid_data)

def _plot_grids_in_row(grids, titles=None):
    """Plots a list of grids in a single row."""
    num_grids = len(grids)
    fig, axs = plt.subplots(1, num_grids, figsize=(4 * num_grids, 4))
    if num_grids == 1:
        axs = [axs]  # Make it iterable for consistency
    
    rgb_grids = [_convert_to_rgb(grid) for grid in grids]

    for i, grid in enumerate(rgb_grids):
        _plot_grid(axs[i], grid)
        if titles and i < len(titles):
            axs[i].set_title(titles[i])

    plt.tight_layout()
    plt.show()

def _plot_multiple_pairs(pairs):
    """Plots multiple pairs of grids, each pair in its own row."""
    num_pairs = len(pairs)
    fig, axs = plt.subplots(num_pairs, 2, figsize=(8, 4 * num_pairs))
    if num_pairs == 1:
        axs = [axs] # Make it iterable

    for i, pair in enumerate(pairs):
        rgb_input = _convert_to_rgb(pair[0])
        rgb_output = _convert_to_rgb(pair[1])
        
        ax_input = axs[i][0]
        ax_output = axs[i][1]
        
        _plot_grid(ax_input, rgb_input)
        ax_input.set_title(f"Pair {i+1}: Input")
        
        _plot_grid(ax_output, rgb_output)
        ax_output.set_title(f"Pair {i+1}: Output")
        
    plt.tight_layout()
    plt.show()

def _convert_to_rgb(data):
    """Converts a grid of color indices to an RGB grid."""
    if not isinstance(data, list) or not data:
        return []
    return [[colors_rgb[value] for value in row] for row in data]

def plot_data(data):
    """
    Plots ARC grids. Dispatches to the appropriate plotting function based on data structure.
    - Single grid: [[]]
    - List of grids (e.g., triplet): [[[]], [[]], [[]]]
    - List of pairs: [[input, output], [input, output]]
    """
    if not isinstance(data, list):
        print("Invalid data format: Input must be a list.")
        return
    
    # Check for a list of pairs
    is_list_of_pairs = all(isinstance(item, list) and len(item) == 2 and isinstance(item[0], list) and isinstance(item[0][0], list) for item in data)
    
    # Check for a single grid
    is_single_grid = all(isinstance(row, list) and all(isinstance(val, int) for val in row) for row in data)
    
    # Check for a list of grids (e.g., a pair or triplet)
    is_list_of_grids = all(isinstance(grid, list) and all(isinstance(row, list) for row in grid) for grid in data) and not is_list_of_pairs

    if is_single_grid:
        _plot_grids_in_row([data], titles=["Grid"])
    elif is_list_of_grids:
        titles = []
        if len(data) == 2:
            titles = ["Input", "Output"]
        elif len(data) == 3:
            titles = ["Input", "Expected Output", "Generated Output"]
        _plot_grids_in_row(data, titles=titles)
    elif is_list_of_pairs:
        _plot_multiple_pairs(data)
    else:
        # Fallback for complex structures or debugging
        print("Unrecognized data structure for plotting.")

# Keep old functions for now to avoid breaking other parts of the codebase.
# They can be removed after confirming everything works with the new structure.
def convert_data(datas, dim):
    return datas # No-op for now
def spliter_full(grid):
    return grid
def detected_object_reform(datas):
    return datas


# if __name__ == "__main__":
#     color_pallette = [[0,1,2,3], [4,5,6,7], [8,9,10,11], [-1,-1,-1,-1]] # 3 additional colors 10 and 11 and 12(-1) [12 means null]
#     # plot_data(color_pallette)

#     arc = ARCDataset()
#     tasks, j_codes = arc.load_data(type = 'train', form = 'list', shuffle = False, jcode = True)

#     x = 14     # 0 - 399      (task number) 37
#     tt = 1    # 0 or 1       (train or test)
#     p = 0     # 0 - max pair (pair number)
#     io = 0    # 0 or 1       (input or output)

#     ex = tasks[x][tt][p][io]

#     plot_data(ex)
#     plot_data(ex, keyword = "tencolorsplit")

#     ex_obj = [[[0]], [[2]], [[0], [0], [0], [0]], [[4]], [[3]], [[8]], [[0, 0, 0, 0]], [[12, 8, 12, 12], [8, 8, 12, 8], [12, 12, 8, 12], [12, 12, 8, 8]], [[0], [0], [0], [0]], [[6]], [[0, 0, 0, 0]], [[12, 12, 0, 0], [12, 12, 0, 12], [0, 0, 12, 0], [12, 0, 12, 12]], [[0, 8, 0, 0], [8, 8, 0, 8], [0, 0, 8, 0], [8, 0, 8, 8]], [[8]], [[12, 8], [8, 8]], [[0, 0], [12, 0]], [[0]], [[0, 0], [0, 12]], [[8, 12], [8, 8]], [[12, 1, 12, 12, 12, 12, 1, 12], [1, 1, 1, 1, 1, 1, 1, 1], [12, 1, 12, 12, 12, 12, 1, 12], [12, 1, 12, 12, 12, 12, 1, 12], [12, 1, 12, 12, 12, 12, 1, 12], [12, 1, 12, 12, 12, 12, 1, 12], [1, 1, 1, 1, 1, 1, 1, 1], [12, 1, 12, 12, 12, 12, 1, 12]], [[2, 1, 0, 0, 0, 0, 1, 3], [1, 1, 1, 1, 1, 1, 1, 1], [0, 1, 0, 8, 0, 0, 1, 0], [0, 1, 8, 8, 0, 8, 1, 0], [0, 1, 0, 0, 8, 0, 1, 0], [0, 1, 8, 0, 8, 8, 1, 0], [1, 1, 1, 1, 1, 1, 1, 1], [4, 1, 0, 0, 0, 0, 1, 6]]]
#     print(len(ex_obj))
#     plot_data(ex_obj, keyword = "objects")