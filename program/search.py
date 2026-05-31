"""
우선순위 탐색 엔진 (뼈대) — property 를 설명하는 *move* 들을 *우선순위* 로 시도한다.

각 move = 한 비교 전략. (scope, mode) 가 그 move 의 성격이자 *선택 이유*:
  · scope: intra(한 부모 안 G0↔G1, 좁음) / inter(부모 간, 넓음)
  · mode : elemental(요소값 비교) / relational(관계: 입력+오프셋 등)
우선순위(작을수록 먼저): **좁은·요소(intra) → 넓은·요소(inter) → 관계(relational)**.
property 마다 우선순위대로 move 를 시도해, *첫 번째로 설명되는* move 가 그 property 의 binding.

지금은 move 3개를 손으로 둔다 — 이게 "kind 영원히 추가"를 *일반화한 뼈대*다. 추후:
  · 각 move 의 detect 를 *원자(IN/CONST/ADD…) 조합 탐색* 으로 (brute 아닌 우선순위 탐색),
  · scope/level 선택·하강도 같은 우선순위 틀로,
확장한다. (지금은 현 문제와 비슷한 결과를 내는 최소 뼈대.)
"""


def _single_offset(examples: list, k: str):
    """단일-셀 좌표류: 모든 pair 의 (출력 − 입력) 오프셋이 동일하면 [dr,dc], 아니면 None."""
    offs = []
    for inp, out in examples:
        ic, oc = inp.get(k), out[k]
        if not (isinstance(ic, list) and isinstance(oc, list) and len(ic) == len(oc) == 1):
            return None
        (ir, icol), (orow, ocol) = ic[0], oc[0]
        offs.append((orow - ir, ocol - icol))
    return list(offs[0]) if all(o == offs[0] for o in offs) else None


def _detect_from_g0(examples, k):
    """intra(좁은 scope, 요소): 출력 == 같은 pair 입력 → 입력 그대로."""
    return {"kind": "from_g0", "attr": k} if all(out[k] == inp.get(k) for inp, out in examples) else None


def _detect_const(examples, k):
    """inter(넓은 scope, 요소): 모든 출력 동일 → 고정값."""
    outs = [out[k] for _, out in examples]
    return {"kind": "const", "value": outs[0]} if all(o == outs[0] for o in outs) else None


def _detect_offset(examples, k):
    """relational(관계): 출력 == 입력 + 동일 오프셋."""
    off = _single_offset(examples, k)
    return {"kind": "g0_offset", "attr": k, "offset": off} if off is not None else None


# 우선순위 순 (priority 작을수록 먼저). scope/mode = 그 move 의 성격이자 선택 이유.
MOVES = [
    {"name": "from_g0",   "priority": 1, "scope": "intra", "mode": "elemental",  "detect": _detect_from_g0},
    {"name": "const",     "priority": 2, "scope": "inter", "mode": "elemental",  "detect": _detect_const},
    {"name": "g0_offset", "priority": 3, "scope": "inter", "mode": "relational", "detect": _detect_offset},
]


def explain_property(examples: list, k: str) -> dict:
    """우선순위대로 move 를 시도 → 첫 설명을 binding 으로 (없으면 unexplained).
    binding 에 via/scope/mode 를 기록 = '왜 이렇게 설명했나'(선택 이유)."""
    for mv in sorted(MOVES, key=lambda m: m["priority"]):
        b = mv["detect"](examples, k)
        if b is not None:
            b.update(via=mv["name"], scope=mv["scope"], mode=mv["mode"])
            return b
    return {"kind": "unexplained"}
