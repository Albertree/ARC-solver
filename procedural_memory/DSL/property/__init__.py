"""
property DSL — ARCKG 노드 to_json() 키를 함수형으로 노출 (재계산 ✗, 노출 ○).

*계층별로* 묶는다 (property 는 그 입력 노드의 계층에 속한다):

  TASK-level   : pair_count                                              (Task 1)
  PAIR-level   : grid_count                                              (Pair 1)
  GRID-level   : size, color, contents                                  (ARCKG Grid 3)
  OBJECT-level : area_of, color_of, coordinate_of, method_of,           (ARCKG Object 8)
                 position_of, shape_of, size_of, symmetry_of
  PIXEL-level  : pixel_color, pixel_coordinate                          (ARCKG Pixel 2)

(각 함수의 입력 타입 = 그 property 의 계층. registry SPECS 의 in[0] 으로도 계층을 안다.)
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


# ── OBJECT-level (ARCKG Object 8 property) ──────────────────
@dsl("property", ["object"], "area")
def area_of(obj):
    """객체 셀 수 (bbox 내 비투명)."""
    return obj.to_json()["area"]


@dsl("property", ["object"], "color-set")
def color_of(obj):
    """객체 색 집합 {0..9: bool}."""
    return obj.to_json()["color"]


@dsl("property", ["object"], "coordinate")
def coordinate_of(obj):
    """객체가 차지한 셀 절대좌표 목록 [[r,c],...]."""
    return obj.to_json()["coordinate"]


@dsl("property", ["object"], "method")
def method_of(obj):
    """객체 추출 방법 {univalued, diagonal, without_bg}."""
    return obj.to_json()["method"]


@dsl("property", ["object"], "position")
def position_of(obj):
    """객체 bbox 네 모서리 좌표 {left_top, right_top, left_bottom, right_bottom}."""
    return obj.to_json()["position"]


@dsl("property", ["object"], "shape")
def shape_of(obj):
    """객체 bbox 모양 2D (비투명=1, 투명=-1)."""
    return obj.to_json()["shape"]


@dsl("property", ["object"], "size")
def size_of(obj):
    """객체 bbox 크기 {height, width}."""
    return obj.to_json()["size"]


@dsl("property", ["object"], "symmetry")
def symmetry_of(obj):
    """객체 대칭 {hori, verti, diag, anti}."""
    return obj.to_json()["symmetry"]


# ── PIXEL-level (ARCKG Pixel 2 property) ────────────────────
@dsl("property", ["pixel"], "color")
def pixel_color(px):
    """픽셀 색 (단일 값)."""
    return px.to_json()["color"]


@dsl("property", ["pixel"], "coordinate")
def pixel_coordinate(px):
    """픽셀 좌표 {row_index, col_index}."""
    return px.to_json()["coordinate"]
