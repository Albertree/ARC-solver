"""
DSL type schema: argument names → types for each DSL function.
Types are named to align with ARCKG (e.g. Coordinate, ColorIndex) so that
AST/context can attach semantic types to keyword arguments.

ARCKG-aligned type names (conceptual):
- Coordinate: (row_index, column_index)
- List[Coordinate]: selection, list of coords
- ColorIndex: int 0..9 (ARC color palette index)
- GridRef: variable name referring to a GRID (e.g. tfg0, main_grid)
"""

# Type names used in schema (string identifiers for AST/ARCKG alignment)
TYPE_COORDINATE = "Coordinate"
TYPE_LIST_COORDINATE = "List[Coordinate]"
TYPE_COLOR_INDEX = "ColorIndex"
TYPE_GRID_REF = "GridRef"
TYPE_INT = "int"
TYPE_STR = "str"
TYPE_LIST_COLOR = "List[ColorIndex]"

# apply_DSL itself: first two are special
APPLY_DSL_MAIN_GRID_TYPE = TYPE_GRID_REF
APPLY_DSL_FUNC_TYPE = "DSLFunction"

# Per-function argument schema: func_name -> { arg_name -> type_name }
DSL_FUNC_SCHEMA = {
    "coloring": {
        "selection": TYPE_LIST_COORDINATE,
        "color": TYPE_COLOR_INDEX,
    },
    "make_grid": {
        "height": TYPE_INT,
        "width": TYPE_INT,
        "color_to_fill": TYPE_COLOR_INDEX,
    },
    "color_switch": {
        "selection": TYPE_LIST_COORDINATE,
        "color1": TYPE_COLOR_INDEX,
        "color2": TYPE_COLOR_INDEX,
    },
    "add_added_color": {
        "colorlist": TYPE_LIST_COLOR,
        "color": TYPE_COLOR_INDEX,
    },
    "add_removed_color": {
        "colorlist": TYPE_LIST_COLOR,
        "color": TYPE_COLOR_INDEX,
    },
    # Add more as needed: rotate, line_flip, move, etc.
}


def get_arg_type(func_name: str, arg_name: str):
    """Return DSL type for (func, arg), or None if unknown."""
    if func_name == "apply_DSL":
        if arg_name == "main_grid":
            return APPLY_DSL_MAIN_GRID_TYPE
        if arg_name == "func":
            return APPLY_DSL_FUNC_TYPE
        return None
    schema = DSL_FUNC_SCHEMA.get(func_name, {})
    return schema.get(arg_name)
