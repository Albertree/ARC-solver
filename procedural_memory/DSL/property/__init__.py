"""
property DSL — ARCKG 노드 to_json() 키를 함수형으로 노출 (재계산 ✗, 노출 ○).

Slice 1 은 GRID 에서 끝나므로 object/pixel property 는 불필요 (SLICE_1_DEV §6).
"""

from procedural_memory.DSL.registry import dsl


@dsl("property", ["task"], "int")
def pair_count(task):
    """task 의 pair 수 (example + test)."""
    j = task.to_json()
    return j["example_pair_count"] + j["test_pair_count"]


@dsl("property", ["pair"], "int")
def grid_count(pair):
    """pair 의 grid 수 (2=in+out, 1=in only)."""
    return pair.to_json()["grid_count"]


@dsl("property", ["grid"], "size")
def size(grid):
    """grid 크기 {height, width}."""
    return grid.to_json()["size"]


@dsl("property", ["grid"], "color-set")
def color(grid):
    """grid 에 등장하는 색 집합 {0..9: bool}."""
    return grid.to_json()["color"]


@dsl("property", ["grid"], "contents")
def contents(grid):
    """grid 의 원시 2D 배열."""
    return grid.to_json()["contents"]
