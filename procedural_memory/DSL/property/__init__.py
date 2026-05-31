"""
property DSL — ARCKG 노드 to_json() 키를 함수형으로 노출 (재계산 ✗, 노출 ○).

*계층별로* 묶는다 (property 는 그 입력 노드의 계층에 속한다):

  TASK-level   : pair_count
  PAIR-level   : grid_count
  GRID-level   : size, color, contents
  OBJECT-level : color_of, coordinate_of, size_of, area_of

(각 함수의 입력 타입 = 그 property 의 계층. registry SPECS 의 in[0] 으로도 계층을 안다.)
PIXEL-level property 는 아직 불필요 — 도입 시 여기 같은 자리에.
"""

from procedural_memory.DSL.registry import dsl


# ── TASK-level ──────────────────────────────────────────────
@dsl("property", ["task"], "int")
def pair_count(task):
    """task 의 pair 수 (example + test)."""
    j = task.to_json()
    return j["example_pair_count"] + j["test_pair_count"]


# ── PAIR-level ──────────────────────────────────────────────
@dsl("property", ["pair"], "int")
def grid_count(pair):
    """pair 의 grid 수 (2=in+out, 1=in only)."""
    return pair.to_json()["grid_count"]


# ── GRID-level ──────────────────────────────────────────────
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


# ── OBJECT-level ────────────────────────────────────────────
@dsl("property", ["object"], "color-set")
def color_of(obj):
    """객체 색 집합 {0..9: bool}."""
    return obj.to_json()["color"]


@dsl("property", ["object"], "coordinate")
def coordinate_of(obj):
    """객체가 차지한 셀 좌표 목록 [[r,c],...]."""
    return obj.to_json()["coordinate"]


@dsl("property", ["object"], "size")
def size_of(obj):
    """객체 bounding-box 크기 {height, width}."""
    return obj.to_json()["size"]


@dsl("property", ["object"], "area")
def area_of(obj):
    """객체 셀 수."""
    return obj.to_json()["area"]
