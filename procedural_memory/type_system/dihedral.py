"""
Dihedral group D4 변환 — 2D 격자 회전/반사.

사용처:
  - shape 비교 (compare_dispatch._compare_shape)
      두 mask가 8개 변환 중 어느 것에서 일치하는지 모음
  - OBJECT.symmetry
      자기 자신이 특정 축 변환에 대해 invariant 인지 검사

8 alternate 순서 (사용자 지정):
  0  identity
  1  flip_h            (좌우 대칭, 세로축 기준)
  2  cw90              (시계방향 90°)
  3  cw90  + flip_v    (cw90 한 뒤 상하 대칭)
  4  cw180
  5  cw180 + flip_h
  6  cw270
  7  cw270 + flip_v
"""


def identity(g):
    return [list(row) for row in g]


def flip_h(g):
    """좌우 대칭 — 각 행을 뒤집음."""
    return [list(reversed(row)) for row in g]


def flip_v(g):
    """상하 대칭 — 행 순서를 뒤집음."""
    return [list(row) for row in reversed(g)]


def cw90(g):
    """시계방향 90° 회전. (HxW → WxH)"""
    if not g or not g[0]:
        return [list(row) for row in g]
    H = len(g)
    W = len(g[0])
    return [[g[H - 1 - c][r] for c in range(H)] for r in range(W)]


def cw180(g):
    return cw90(cw90(g))


def cw270(g):
    return cw90(cw180(g))


def flip_diag(g):
    """주 대각선 대칭 (transpose). 정사각형 전용."""
    n = len(g)
    return [[g[c][r] for c in range(n)] for r in range(n)]


def flip_anti(g):
    """반 대각선 대칭. 정사각형 전용."""
    n = len(g)
    return [[g[n - 1 - c][n - 1 - r] for c in range(n)] for r in range(n)]


def alternates(g):
    """8 alternate를 사용자 지정 순서로 반환.
       index 0~7 의 의미는 모듈 docstring 참조."""
    base_0 = identity(g)
    base_2 = cw90(g)
    base_4 = cw180(g)
    base_6 = cw270(g)
    return [
        base_0,
        flip_h(base_0),
        base_2,
        flip_v(base_2),
        base_4,
        flip_h(base_4),
        base_6,
        flip_v(base_6),
    ]
