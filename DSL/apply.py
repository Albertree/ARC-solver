from DSL.transformation import *
from DSL.util import *
from ARCKG.grid import GRID
from DSL.selection import SELECTION
from basics.utils import printcg
from DSL.layer import merge_layers, paste_sub_array, make_selection_layer, make_mask, make_edit_space, make_layer, make_trimmed_grid

# NEW apply_DSL function with kwargs support and DSL type distinction
def apply_DSL(main_grid, func, **kwargs):
    """
    Apply DSL function with kwargs support.
    Preferred call: apply_DSL(main_grid=..., func=..., **kwargs) so AST has explicit keys for typing.

    Args:
        main_grid: GRID object
        func: DSL function to apply
        **kwargs: Function arguments (e.g. selection=..., color=...)

    Returns:
        For transformation DSL: GRID object (trimmed result)
        For util DSL: main_grid (side effects only)
    """
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

    # Build accumulated layers from main_grid (GRID)
    frame_size = (main_grid.width, main_grid.height)
    edit_space = make_edit_space()
    main_grid_layer = paste_sub_array(make_layer(), (30, 30), main_grid.raw_data)
    mask = make_mask(main_grid.height, main_grid.width)
    accumulated_layers = [edit_space, main_grid_layer, mask]

    if is_transformation and func != make_grid:
        selection_coords = kwargs.get('selection')
        if selection_coords is None:
            raise ValueError(f"Selection is required for transformation function {func.__name__}")
        selection = SELECTION(selection_coords, main_grid)
        selection_layer = make_selection_layer(selection, with_color_from_main_grid=True)
        kwargs['selection'] = selection

    if is_transformation:
        if func == make_grid:
            applied_layer = func(**kwargs)
        else:
            applied_layer = func(**kwargs)
        accumulated_layers.insert(-1, applied_layer)
        keep_original = True
        merged_layer = merge_layers(accumulated_layers, keep_original)
        if func == make_grid:
            height = kwargs.get('height')
            width = kwargs.get('width')
            mask = make_mask(width, height)
            accumulated_layers[-1] = mask
        else:
            mask = make_mask(frame_size[0], frame_size[1])
        trimmed_grid = make_trimmed_grid(merged_layer, mask)
        # Return GRID with trimmed result (same parent as main_grid)
        result = GRID(
            id=main_grid.id,
            type=main_grid.type,
            parent=main_grid.parent,
            raw_data=trimmed_grid
        )
        result.update_property()
        return result

    elif is_util:
        func(**kwargs)
        return main_grid