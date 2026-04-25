"""
dsl/primitives — ARC 변환을 위한 두 가지 기본 DSL 함수.

모든 transformation은 이 두 함수의 조합으로 표현된다.
다른 transformation 함수를 추가하지 않는다.
"""

from __future__ import annotations

import copy


def coloring(grid: list[list[int]], selection, color: int) -> list[list[int]]:
    """
    그리드의 특정 위치를 지정한 색으로 칠한다.

    Args:
        grid: 2D int 배열 (in-place 수정하지 않고 복사본 반환)
        selection: [row, col] 단일 좌표 또는 [[row, col], ...] 좌표 리스트
        color: 0-9 (ARC 색상) 또는 13 (투명/배경색으로 덮어씀 → 0)

    Returns:
        수정된 grid 복사본
    """
    result = copy.deepcopy(grid)
    h = len(result)
    w = len(result[0]) if h > 0 else 0

    # 실제 칠할 색상: 13(투명)이면 배경색 0으로 처리
    paint_color = 0 if color == 13 else color

    # selection 정규화: 단일 좌표면 리스트로 감싼다
    if not selection:
        return result
    if isinstance(selection[0], (int, float)):
        coords = [selection]
    else:
        coords = selection

    for coord in coords:
        r, c = int(coord[0]), int(coord[1])
        if 0 <= r < h and 0 <= c < w:
            result[r][c] = paint_color

    return result


def make_grid(height: int, width: int, color: int) -> list[list[int]]:
    """
    새로운 그리드를 생성한다.

    Args:
        height: 행 수
        width: 열 수
        color: 배경색 (0-9 또는 13 → 0)

    Returns:
        height×width 2D int 배열
    """
    fill = 0 if color == 13 else color
    return [[fill] * width for _ in range(height)]
