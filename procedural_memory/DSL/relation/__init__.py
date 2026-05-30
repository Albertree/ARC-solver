"""
relation DSL — 모듈 C: scope selector(select) + 비교(compare / compare_set).

모든 비교는 compare(scope) 통일형 (SLICE_1_DEV §6). 모듈은 *level-agnostic* —
어떤 scope 를 넘기느냐로 흐름 라벨이 정해진다:
  · Inter-Pair        : pair 끼리 비교 (pair property, 예: grid-count)
  · Inter-Pair-Grid   : 다른 pair 에 속한 grid 끼리 비교 (예: P0.G1 ↔ P1.G1)
즉 비교는 전부 "Inter-[level]" — 같은 레벨 노드들의 property 비교다.

주의: "Intra-[component]" 는 *비교가 아니다*. pair 등 현재 레벨 정보로 목적 달성이
불가능해 더 깊은 레벨로 내려가는 *descent* (= "intra-pair analysis") 이며, 모듈 A
(단계 3) 소관이다. 여기 C 에는 두지 않는다.

C–D 결합: select 가 D(util)를 호출, compare 는 ARCKG/comparison.py 재사용.
"""

from itertools import combinations

from ARCKG.comparison import compare as _kg_compare
from procedural_memory.DSL.registry import dsl
from procedural_memory.DSL.util import pairs_of, grids_of, filter_

# level → anchor 아래 그 level 원소를 주는 util
_LEVEL_CHILDREN = {"pair": pairs_of, "grid": grids_of}


@dsl("util", ["anchor", "level"], "list[node]")
def elements_at(anchor, level):
    """anchor 아래 level 의 원소들 (util 디스패치)."""
    return _LEVEL_CHILDREN[level](anchor)


@dsl("relation", ["anchor", "level", "pred"], "scope")
def select(anchor, level, pred=None):
    """scope = filter(elements-at(anchor, level), pred)."""
    items = elements_at(anchor, level)
    return filter_(items, pred) if pred is not None else list(items)


@dsl("relation", ["node", "node"], "receipt")
def compare(a, b):
    """두 노드 비교 → receipt. ARCKG/comparison.py 재사용.
    score = COMM property 개수 / 전체 property 개수 (comparison.py 가 계산)."""
    return _kg_compare(a, b)


@dsl("relation", ["scope"], "receipts")
def compare_set(nodes):
    """같은 레벨 노드 집합(scope)을 pairwise 비교 → [(x, y, receipt), ...].
    Inter-Pair = compare_set(pairs), Inter-Pair-Grid = compare_set(role-aligned grids)."""
    return [(x, y, compare(x, y)) for x, y in combinations(nodes, 2)]


def verdict(receipt) -> tuple:
    """receipt 판정 요약: (type, score=comm/total, COMM 인 property 키 목록)."""
    res = receipt["result"]
    comm = [k for k, v in res.get("category", {}).items()
            if isinstance(v, dict) and v.get("type") == "COMM"]
    return res["type"], res["score"], comm
