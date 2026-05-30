"""
util DSL — 노드 계층 항해·필터 (Slice 1, SLICE_1_DEV §6).

ARCKG 노드 구조를 함수형으로 노출만 한다 (계산 로직 없음).
"""

from procedural_memory.DSL.registry import dsl


@dsl("util", ["task"], "list[pair]")
def pairs_of(task):
    """task 의 모든 pair (example 먼저, 그다음 test)."""
    return list(task.example_pairs) + list(task.test_pairs)


@dsl("util", ["pair"], "list[grid]")
def grids_of(pair):
    """pair 의 grid 들 (G0=input, 있으면 G1=output)."""
    grids = [pair.input_grid]
    if pair.output_grid is not None:
        grids.append(pair.output_grid)
    return grids


@dsl("util", ["grid"], "role")
def role_of(grid):
    """grid 역할 — node_id 끝 세그먼트로 판정: G0=input, G1=output."""
    last = grid.node_id.split(".")[-1]
    if last == "G0":
        return "input"
    if last == "G1":
        return "output"
    return last


@dsl("util", ["set", "pred"], "set")
def filter_(items, pred):
    """pred(x) 가 참인 원소만 남긴다."""
    return [x for x in items if pred(x)]
