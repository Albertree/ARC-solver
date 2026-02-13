from DSL.transformation import *
from DSL.util import *
from ARCKG.tf_grid import TF_GRID, TF_GRIDInfo
from DSL.selection import SELECTION
from basics.utils import printcg
from DSL.layer import merge_layers, paste_sub_array, make_selection_layer, make_mask, make_edit_space, make_layer

# def check_args(main_grid, func, *args):
#     if func == make_grid:
#         return None, *args[0:]
#     elif func == coloring:
#         selection = SELECTION(args[0], main_grid)
#         return selection, *args[1:]
    
#     elif func == color_switch:
#         selection = SELECTION(args[0], main_grid)

#         return selection, *args[1:]
#     else:
#         return args
    
# OLD apply_DSL function - commented out
# def apply_DSL(main_grid, func, *args, **kwargs):
#     if type(main_grid) == TF_GRID:
#         frame_size = (len(main_grid.trimmed_grid[0]), len(main_grid.trimmed_grid))
#         accumulated_layers = main_grid.accumulated_layers
#     else:
#         frame_size = (main_grid.width, main_grid.height)
#         edit_space = make_edit_space()
#         main_grid_layer = paste_sub_array(make_layer(), (30, 30), main_grid.raw_data)
#         mask = make_mask(main_grid.height, main_grid.width)
#         accumulated_layers = [edit_space, main_grid_layer, mask]
#     if func == make_grid:
#         selection = None
#     else:
#         print(f"DEBUG: Creating SELECTION with args[0] = {args[0]}, type = {type(args[0])}")
#         selection = SELECTION(args[0], main_grid)
#         selection_layer = make_selection_layer(selection, with_color_from_main_grid=True)
#         selection_layer2 = make_selection_layer(selection, with_color_from_main_grid=False)
#     # 3. Apply DSL
#     if func == make_grid:
#         applied_layer = func(None, *args[0:], **kwargs)
#     else:
#         applied_layer = func(selection_layer, selection, *args[1:], **kwargs)
#     accumulated_layers.insert(-1, applied_layer)
#     # 3.5 Keep the original or not
#     keep_original = True
#     # 4. Merge Layers
#     merged_layer = merge_layers(accumulated_layers, keep_original)
#     if func == make_grid:
#         mask = make_mask(args[0], args[1])
#         accumulated_layers[-1] = mask
#     else:
#         mask = make_mask(frame_size[0], frame_size[1])
#     # Crop the layer using list comprehension
#     trimmed_grid = TF_GRID.make_trimmed_grid(merged_layer, mask)
#     # 새로운 TF_GRID ID 생성
#     new_tf_grid_id = TF_GRID.get_next_id()
#     tfg_grid_info = TF_GRIDInfo(
#         id = new_tf_grid_id,
#         type = "tfgrid",
#         raw_data = trimmed_grid
#     )
#     result = TF_GRID.from_json(tfg_grid_info, accumulated_layers, main_grid.parent)
#     return result

# NEW apply_DSL function with kwargs support and DSL type distinction
def apply_DSL(main_grid, func, **kwargs):
    """
    Apply DSL function with kwargs support.
    
    Args:
        main_grid: TF_GRID or GRID object
        func: DSL function to apply
        **kwargs: Function arguments
    
    Returns:
        For transformation DSL: TF_GRID object
        For util DSL: None (side effects only)
    """
    
    # Determine if this is a transformation or util DSL function
    transformation_functions = {
        make_grid, coloring, color_switch, rotate, line_flip, point_flip, 
        move, teleport, connect, straight_line, rectangle, crop
    }
    
    util_functions = {
        add_added_color, add_removed_color
    }
    
    is_transformation = func in transformation_functions
    is_util = func in util_functions
    
    if not (is_transformation or is_util):
        raise ValueError(f"Unknown DSL function: {func}")
    
    # Handle input grid type
    if type(main_grid) == TF_GRID:
        frame_size = (len(main_grid.trimmed_grid[0]), len(main_grid.trimmed_grid))
        accumulated_layers = main_grid.accumulated_layers
    else:
        frame_size = (main_grid.width, main_grid.height)
        edit_space = make_edit_space()
        main_grid_layer = paste_sub_array(make_layer(), (30, 30), main_grid.raw_data)
        mask = make_mask(main_grid.height, main_grid.width)
        accumulated_layers = [edit_space, main_grid_layer, mask]
    
    # Handle selection for transformation DSL functions (except make_grid)
    if is_transformation and func != make_grid:
        selection_coords = kwargs.get('selection')
        if selection_coords is None:
            raise ValueError(f"Selection is required for transformation function {func.__name__}")
        
        selection = SELECTION(selection_coords, main_grid)
        selection_layer = make_selection_layer(selection, with_color_from_main_grid=True)
        
        # Add selection to kwargs for the function
        kwargs['selection'] = selection
    
    # Apply the DSL function
    if is_transformation:
        if func == make_grid:
            applied_layer = func(**kwargs)
        else:
            applied_layer = func(**kwargs)
        
        # Add the applied layer to accumulated layers
        accumulated_layers.insert(-1, applied_layer)
        
        # Merge layers
        keep_original = True
        merged_layer = merge_layers(accumulated_layers, keep_original)
        
        # Create mask
        if func == make_grid:
            height = kwargs.get('height')
            width = kwargs.get('width')
            mask = make_mask(width, height)
            accumulated_layers[-1] = mask
        else:
            mask = make_mask(frame_size[0], frame_size[1])
        
        # Crop the layer
        trimmed_grid = TF_GRID.make_trimmed_grid(merged_layer, mask)
        
        # Create new TF_GRID
        new_tf_grid_id = TF_GRID.get_next_id()
        tfg_grid_info = TF_GRIDInfo(
            id = new_tf_grid_id,
            type = "tfgrid",
            raw_data = trimmed_grid
        )
        
        result = TF_GRID.from_json(tfg_grid_info, accumulated_layers, main_grid.parent)
        return result
    
    elif is_util:
        # For util functions, just execute and return the original main_grid
        func(**kwargs)
        return main_grid