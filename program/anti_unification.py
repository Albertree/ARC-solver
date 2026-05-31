"""
anti_unification — example 들의 산물을 across-pair 로 일반화해 *schema* 를 뽑는다.

각 출력 property 를 일반화:
  · 모든 example 출력에서 동일        → const     (고정값)
  · pair 마다 출력 = 같은 pair 입력     → from_g0   (입력 그대로 복사)
  · pair 마다 출력 = 입력 + 동일 오프셋  → g0_offset (입력을 고정량 이동)
  · 그 외                            → unexplained (현 일반화로 설명 불가)

※ 알려진 한계(논의 중): "종류(kind)"를 손으로 늘리는 방식은 일반적이지 않다.
  궁극적으로는 입력→출력 변환을 *DSL 합성*으로 *탐색* 해 찾아야 한다 (const/from_g0/
  offset 도 그 합성의 특수 사례). 지금은 e·f 를 풀기 위한 잠정 구현.
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


def anti_unify_objects(examples: list, props: list) -> dict:
    """examples: [(in_props, out_props), ...]  (전경 객체 to_json dict 쌍)."""
    schema = {}
    for k in props:
        outs = [out[k] for _, out in examples]
        if all(o == outs[0] for o in outs):
            schema[k] = {"kind": "const", "value": outs[0]}
        elif all(out[k] == inp.get(k) for inp, out in examples):
            schema[k] = {"kind": "from_g0", "attr": k}
        elif (off := _single_offset(examples, k)) is not None:
            schema[k] = {"kind": "g0_offset", "attr": k, "offset": off}
        else:
            schema[k] = {"kind": "unexplained"}
    return schema


def is_solvable(schema: dict) -> bool:
    """schema 의 모든 property 가 설명됨(unexplained 아님)이면 True."""
    return all(e["kind"] != "unexplained" for e in schema.values())


def resolve_property(entry: dict, test_props: dict):
    """schema 항목 + test 입력 property → 구체값."""
    if entry["kind"] == "const":
        return entry["value"]
    if entry["kind"] == "from_g0":
        return test_props[entry["attr"]]
    if entry["kind"] == "g0_offset":
        dr, dc = entry["offset"]
        return [[r + dr, c + dc] for r, c in test_props[entry["attr"]]]
    raise ValueError(f"unknown schema kind: {entry['kind']}")
