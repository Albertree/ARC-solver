"""
relation DSL — 모듈 C: 비교 (두 노드의 관계 = 공통점·차이점).

compare(a, b)     두 노드 비교 → receipt (공통점/차이점).
compare(scope)    scope(list) 내 pairwise 비교 → [(x, y, receipt), ...].
                  (= 구 compare_set 을 흡수. b 없으면 scope 모드.)

비교할 *범위* 는 selection 의 select 로 정해 넘긴다: compare( select(...) ).
compare 자체는 ARCKG/comparison.py 재사용. receipt 요약은 verdict.
"""

from itertools import combinations

from ARCKG.comparison import compare as _kg_compare
from procedural_memory.DSL.registry import dsl


@dsl("relation", ["a", "b?"], "receipt | receipts")
def compare(a, b=None):
    """b 있으면 두 노드 비교(→receipt). b 없으면 a=scope 의 pairwise(→receipts)."""
    if b is None:
        return [(x, y, _kg_compare(x, y)) for x, y in combinations(a, 2)]
    return _kg_compare(a, b)


def verdict(receipt) -> tuple:
    """receipt 판정 요약: (type, score=comm/total, COMM 인 property 키 목록)."""
    res = receipt["result"]
    comm = [k for k, v in res.get("category", {}).items()
            if isinstance(v, dict) and v.get("type") == "COMM"]
    return res["type"], res["score"], comm
