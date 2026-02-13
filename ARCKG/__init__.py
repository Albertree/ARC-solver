"""
ARCKG: ARC Knowledge Graph components and comparison.

Usage:
  from ARCKG import TASK, PAIR, GRID, compare
  task = ...
  compare(task.example_pairs[0].input_grid, task.example_pairs[0].output_grid, save=True)
"""

# Comparison first (no dependency on other ARCKG submodules at import time)
from ARCKG.comparison import (
    compare,
    get_comparison_data,
    get_component_full_id,
    id_to_json_path,
    id_pair_to_comparison_path,
    json_path_to_id,
    save_comparison_result,
)

from ARCKG.task import TASK, TASKInfo
from ARCKG.pair import PAIR, PAIRInfo
from ARCKG.grid import GRID, GRIDInfo
from ARCKG.object import OBJECT, OBJECTInfo
from ARCKG.pixel import PIXEL, PIXELInfo

__all__ = [
    "TASK", "TASKInfo",
    "PAIR", "PAIRInfo",
    "GRID", "GRIDInfo",
    "OBJECT", "OBJECTInfo",
    "PIXEL", "PIXELInfo",
    "compare",
    "get_comparison_data",
    "get_component_full_id",
    "id_to_json_path",
    "id_pair_to_comparison_path",
    "json_path_to_id",
    "save_comparison_result",
]
