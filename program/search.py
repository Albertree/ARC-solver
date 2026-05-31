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

── 폭증/오버피팅 제어 ──
  ① 좌표는 *통째로(joint)* 탐색 — component 따로면 degenerate 하게 맞아 오버피팅.
  ② offset 은 예제에서 *풀고*(out−base) 일관성만 확인 (상수 열거 X).
  ③ base 후보·depth 한정 + 첫 적합 멈춤. 발견 조합은 라이브러리 재사용.

설명서 생성: program.search.TRACE 를 list 로 두면 탐색 시도(성공/실패 이유)가 기록된다.
"""

# 설명서 모드: list 면 explain_property 의 각 시도(attempt)를 기록 (평소엔 None=무영향)
TRACE = None


def _rec(**d):
    if TRACE is not None:
        TRACE.append(d)


def _base_value(name: str, ctx: dict) -> list:
    """좌표 합성용 base 벡터 [r-축, c-축]."""
    if name == "in_coord":
        return ctx["coordinate"][0]
    if name == "grid_dims":
        return [ctx["grid_h"], ctx["grid_w"]]
    raise ValueError(f"unknown base: {name}")


_COORD_BASES = ["in_coord", "grid_dims"]   # base 우선순위: 같은 property → cross-property


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

    d = _joint_offset(examples, "in_coord")                 # 1. in_coord + Δ
    _rec(prop="coordinate", attempt="in_coord + Δ (입력 위치 기준 = from_g0/이동)",
         ok=d is not None, detail=(f"모든 pair 에서 (출력−입력) offset = {d} 로 일관"
                                   if d is not None else "pair 마다 (출력−입력) offset 이 달라 불일치"))
    if d is not None:
        return {"kind": "coord", "base": "in_coord", "offset": d, "via": "in_coord+Δ"}

    same = all(o == outs[0] for o in outs)                  # 2. const
    _rec(prop="coordinate", attempt="const (모든 출력 동일)",
         ok=same, detail=(f"모든 출력 위치 = {outs[0]} 고정" if same else f"출력 위치 제각각 {outs}"))
    if same:
        return {"kind": "const", "value": [outs[0]], "via": "const"}

    d = _joint_offset(examples, "grid_dims")                # 3. grid_dims + Δ (corner 등)
    _rec(prop="coordinate", attempt="grid_dims + Δ (grid 크기 기준 = 모서리 등, cross-property)",
         ok=d is not None, detail=(f"(출력−(grid_h,grid_w)) = {d} 로 일관 → 모서리류"
                                   if d is not None else "grid 크기 기준으로도 불일치"))
    if d is not None:
        return {"kind": "coord", "base": "grid_dims", "offset": d, "via": "grid_dims+Δ"}

    return {"kind": "unexplained"}


def explain_property(examples: list, k: str) -> dict:
    """출력 property k 를 우선순위대로 설명 → binding(kind + via=선택 이유)."""
    if k == "coordinate":
        return _explain_coordinate(examples)

    fg0 = all(out[k] == inp.get(k) for inp, out in examples)
    _rec(prop=k, attempt="from_g0 (출력 = 같은 pair 입력)",
         ok=fg0, detail="모든 pair 에서 출력=입력 (보존)" if fg0 else "출력 ≠ 입력")
    if fg0:
        return {"kind": "from_g0", "attr": k, "via": "from_g0"}

    outs = [out[k] for _, out in examples]
    same = all(o == outs[0] for o in outs)
    _rec(prop=k, attempt="const (모든 출력 동일)",
         ok=same, detail="모든 출력 동일 (고정)" if same else "출력 제각각")
    if same:
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
