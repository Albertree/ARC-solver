"""
ARCKG — Knowledge Graph core package.

Public interface:
    Task, Pair, Grid, Object, Pixel   — five-layer KG node classes
    compare                            — core relation-building function
    id_to_json_path                    — node ID → filesystem path
    id_pair_to_comparison_path         — (id_a, id_b) → comparison edge path
"""

from ARCKG.task import Task
from ARCKG.pair import Pair
from ARCKG.grid import Grid
from ARCKG.object import Object
from ARCKG.pixel import Pixel
from ARCKG.comparison import compare
from ARCKG.memory_paths import id_to_json_path, id_pair_to_comparison_path

__all__ = [
    "Task", "Pair", "Grid", "Object", "Pixel",
    "compare",
    "id_to_json_path", "id_pair_to_comparison_path",
]
