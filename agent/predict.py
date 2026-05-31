"""
Predict + K (output / emit_answer).

결정적 비교(descend_to_decisive)의 evidence 로부터 test 출력을 도출한다. 값-agnostic:
정답을 하드코딩하지 않고 *비교 결과* 에서 끌어온다 (P3/P4). evidence 모양에 따라 분기:
  · Slice 1 (모든 G1 COMM): evidence={size, color, contents} → 공통 contents 복사
  · Slice 2 (객체 스키마):  evidence={size, position, color} → make_grid+coloring 조합
"""

from procedural_memory.DSL.transformation import make_grid, coloring


def predict(evidence: dict):
    """evidence → 출력 grid (2D 배열)."""
    if "contents" in evidence:
        # Slice 1: 출력 고정 — 공통 grid 그대로
        return evidence["contents"]
    # Slice 2: schema 가 푼 {size, cells, color} 를 씨앗 2개로 *구성*
    grid = make_grid(evidence["size"], 0)
    for (r, c) in evidence["cells"]:
        grid = coloring(grid, (r, c), evidence["color"])
    return grid


def emit_answer(task, grid) -> list:
    """K (output) — test pair 마다 출력 grid 제출.
    (Slice 1~2 는 test pair 1개. 다중 test·test별 G0 변수는 추후.)"""
    return [grid for _ in task.test_pairs]
