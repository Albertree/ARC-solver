from .transformation_DSL import *
from ARCKG.tf_grid import TF_GRID
from .selection import SELECTION
from basics.utils import printcg
from .layer_utils import merge_layers


def check_args(main_grid, func, *args):
    if func == make_grid:
        return None, *args[0:]
    elif func == coloring:
        selection = SELECTION(args[0], main_grid)
        return selection, *args[1:]
    
    elif func == color_switch:
        selection = SELECTION(args[0], main_grid)

        return selection, *args[1:]
    else:
        return args
    
def apply_DSL(main_grid, func, *args, **kwargs):

    if type(main_grid) == TF_GRID:
        frame_size = (len(main_grid.trimmed_grid[0]), len(main_grid.trimmed_grid))
        accumulated_layers = main_grid.accumulated_layers
    
    else:
        frame_size = (main_grid.width, main_grid.height)
        edit_space = make_edit_space()
        main_grid_layer = paste_sub_array(make_layer(), (30, 30), main_grid.raw_data)
        mask = make_mask(main_grid.height, main_grid.width)
        accumulated_layers = [edit_space, main_grid_layer, mask]

    if func == make_grid:
        selection = None
    else:
        selection = SELECTION(args[0], main_grid)

        selection_layer = make_selection_layer(selection, with_color_from_main_grid=True)
        selection_layer2 = make_selection_layer(selection, with_color_from_main_grid=False)

    # 3. Apply DSL
    if func == make_grid:
        applied_layer = func(None, *args[0:], **kwargs)

    else:
        applied_layer = func(selection_layer, selection, *args[1:], **kwargs)

    accumulated_layers.insert(-1, applied_layer)

    # 3.5 Keep the original or not
    keep_original = True

    # 4. Merge Layers
    merged_layer = merge_layers(accumulated_layers, keep_original)
    
    if func == make_grid:
        mask = make_mask(args[0], args[1])
        accumulated_layers[-1] = mask

    else:
        mask = make_mask(frame_size[0], frame_size[1])
    
    # Crop the layer using list comprehension
    # trimmed_grid = make_trimmed_grid(merged_layer, mask)
    # trimmed_grid = [row[30:30+window_size[1]] for row in merged_layer[30:30+window_size[0]]]
    
    result = TF_GRID(accumulated_layers, main_grid.id, main_grid.id, 2)
    result.update_property()
    result.update_childs()

    # printcg(result.view) ################## UNCOMMENT THIS TO SEE THE RESULT ##################
    return result