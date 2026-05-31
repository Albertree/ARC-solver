"""
우선순위 탐색 엔진 — 출력 property 를 *입력 property들의 원자 조합* 으로 설명한다.

손으로 move(kind)를 나열하는 대신, "어느 입력(base) + 어떤 offset" 인지 *탐색*.
from_g0/const/offset/corner 가 전부 "출력좌표 = (base) + offset" 의 특수 사례 —
하나의 탐색이 흡수한다 (손 추가 없이 새 조합도 발견):
  base=in_coord, off=0    → from_g0
  base=in_coord, off=Δ    → offset
  base=grid_dims, off=-1  → corner(우하단)

우선순위 (가까운 것 먼저, 첫 적합 즉시 채택):
  좌표:  in_coord+Δ  →  const  →  grid_dims+Δ
  기타(color/grid_size): from_g0 → const  (dict 동등성)

── 폭증/오버피팅 제어 (당신 우려의 답) ──
  ① 좌표는 *통째로(joint)* 탐색 — component 따로면 degenerate 하게 맞아 *오버피팅*.
     (e: train in_row 가 다 1이라 row 만 보면 const 로 맞아버림 → 일반화 실패.)
  ② offset 은 예제에서 *풀고*(out−base) 일관성만 확인 (상수 열거 X).
  ③ base 후보·depth 한정 + 첫 적합 멈춤. 발견 조합은 라이브러리 재사용(재탐색 X).
  → 유연성을 늘릴수록 train 적합 ↑·일반화 ↓ 이므로, *작고 우선순위 있게* 가 핵심.
"""


def _base_value(name: str, ctx: dict) -> list:
    """좌표 합성용 base 벡터 [r-축, c-축]."""
    if name == "in_coord":
        return ctx["coordinate"][0]
    if name == "grid_dims":
        return [ctx["grid_h"], ctx["grid_w"]]
    raise ValueError(f"unknown base: {name}")


# base 후보 우선순위: 같은 property(in_coord) → cross-property(grid_dims)
_COORD_BASES = ["in_coord", "grid_dims"]


def _joint_offset(examples, base):
    """모든 예제에서 (out_coord − base) offset 이 동일하면 [Δr,Δc], 아니면 None. (joint)"""
    ds = []
    for inp, out in examples:
        o, b = out["coordinate"][0], _base_value(base, inp)
        ds.append([o[0] - b[0], o[1] - b[1]])
    return ds[0] if all(d == ds[0] for d in ds) else None


def _explain_coordinate(examples):
    """좌표 [[r,c]] 단일 셀을 base+offset 으로 통째 탐색 (우선순위: in_coord → const → grid)."""
    outs = [o["coordinate"][0] for _, o in examples]
    d = _joint_offset(examples, "in_coord")                 # 1. in_coord + Δ (from_g0/offset)
    if d is not None:
        return {"kind": "coord", "base": "in_coord", "offset": d, "via": "in_coord+Δ"}
    if all(o == outs[0] for o in outs):                     # 2. const
        return {"kind": "const", "value": [outs[0]], "via": "const"}
    d = _joint_offset(examples, "grid_dims")                # 3. grid_dims + Δ (corner 등)
    if d is not None:
        return {"kind": "coord", "base": "grid_dims", "offset": d, "via": "grid_dims+Δ"}
    return {"kind": "unexplained"}


def explain_property(examples: list, k: str) -> dict:
    """출력 property k 를 우선순위대로 설명 → binding(kind + via=선택 이유)."""
    if k == "coordinate":
        return _explain_coordinate(examples)
    # color/grid_size 등 dict 값: from_g0(같은 입력) → const
    if all(out[k] == inp.get(k) for inp, out in examples):
        return {"kind": "from_g0", "attr": k, "via": "from_g0"}
    outs = [out[k] for _, out in examples]
    if all(o == outs[0] for o in outs):
        return {"kind": "const", "value": outs[0], "via": "const"}
    return {"kind": "unexplained"}


def resolve_property(binding: dict, test: dict):
    """binding + test 맥락 → 구체값."""
    if binding["kind"] == "const":
        return binding["value"]
    if binding["kind"] == "from_g0":
        return test[binding["attr"]]
    if binding["kind"] == "coord":
        b, off = _base_value(binding["base"], test), binding["offset"]
        return [[b[0] + off[0], b[1] + off[1]]]
    raise ValueError(f"unknown binding kind: {binding['kind']}")
