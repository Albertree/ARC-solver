"""
anti_unification — example 들의 산물을 across-pair 로 일반화해 *schema* 를 뽑는다.

각 출력 property 를 우선순위 탐색 엔진([[program/search]])으로 설명한다 — 즉 어떤
move(from_g0 / const / g0_offset / …)가 그 property 를 설명하는지 *우선순위대로* 찾는다.
schema = {property: binding(kind + via/scope/mode = 선택 이유)}.

"종류(kind)를 손으로 늘리는" 것은 search.MOVES 에 move 를 더하는 잠정 형태 —
추후 각 move 의 detect 가 원자 조합 탐색으로 바뀐다.
"""

from program.search import explain_property


def anti_unify_objects(examples: list, props: list) -> dict:
    """examples: [(in_props, out_props), ...]. 각 property 를 우선순위 move 로 설명."""
    return {k: explain_property(examples, k) for k in props}


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
