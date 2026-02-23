"""
Value DSL: expressions over ARCKG (grid/object/pixel) that the generated
abstract program can call so that v1 = coord_of(object_at_input(input_grid, 0))
evaluates to the right value per pair.

All functions are intended to be used from generated code with `input_grid` in scope.
"""

from typing import List, Tuple, Any


def object_at_input(grid, i: int):
    """i-th object in grid (0-based). grid must have .objects (ARCKG GRID)."""
    if not hasattr(grid, "objects") or not grid.objects:
        return None
    if i < 0 or i >= len(grid.objects):
        return None
    return grid.objects[i]


def left_top_of(obj) -> Tuple[int, int]:
    """Object's top-left position (row, col)."""
    if obj is None or not hasattr(obj, "pos"):
        return (0, 0)
    return tuple(obj.pos) if isinstance(obj.pos, (list, tuple)) else (0, 0)


def selection_left_top_of(obj) -> List[Tuple[int, int]]:
    """Selection (list of one coord) from object's top-left. For apply_DSL(..., selection=...)."""
    return [left_top_of(obj)]


def center_of(obj):
    """Object's center coordinate(s). Returns first center if list."""
    if obj is None or not hasattr(obj, "center"):
        return (0, 0)
    c = obj.center
    if isinstance(c, list) and c:
        return c[0] if isinstance(c[0], (list, tuple)) else c
    return (0, 0)


def coords_of(obj) -> List[Tuple[int, int]]:
    """Object's full coordinate list."""
    if obj is None or not hasattr(obj, "coordinate"):
        return []
    coord = obj.coordinate
    if isinstance(coord, list):
        return [tuple(c) if isinstance(c, (list, tuple)) else c for c in coord]
    return [tuple(coord)]


def color_of(obj) -> Any:
    """Primary color of object (first True in .color dict, or 0)."""
    if obj is None or not hasattr(obj, "color"):
        return 0
    color = obj.color
    if isinstance(color, dict):
        for k, v in color.items():
            if v:
                try:
                    return int(k)
                except (TypeError, ValueError):
                    return k
    if isinstance(color, (int, float)):
        return int(color)
    return 0


def pixel_at_input(grid, row: int, col: int):
    """Pixel at (row, col) in grid. Returns object with .color and .coordinate."""
    if not hasattr(grid, "pixels") or not grid.pixels:
        return None
    w = grid.width if hasattr(grid, "width") else (len(grid.raw_data[0]) if grid.raw_data else 0)
    idx = row * w + col
    if idx < 0 or idx >= len(grid.pixels):
        return None
    return grid.pixels[idx]


def coord_of_pixel(pixel) -> Tuple[int, int]:
    """Pixel's (row, col)."""
    if pixel is None or not hasattr(pixel, "coordinate"):
        return (0, 0)
    c = pixel.coordinate
    return tuple(c) if isinstance(c, (list, tuple)) else (0, 0)


def color_of_pixel(pixel) -> int:
    """Pixel color (int)."""
    if pixel is None or not hasattr(pixel, "color"):
        return 0
    return int(pixel.color)
