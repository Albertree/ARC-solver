"""
DSL 탐색 (모듈 3) — Need 를 들고 '이 상황을 해소할 DSL 이 있나' 를 묻는다.

활성화는 *효과 매칭*: 각 DSL 명세의 effect 가 need.requires 를 해소하는가
(계층이 아니라 효과로 건다 — effect.matches). 탐색의 *조건* 이 곧 해소하려는
상황(need)이다.  비면 [] → 이 scope 에선 못 풂 → 막힘 → 하강 정당화.
"""

from procedural_memory.DSL.registry import SPECS, spec
from procedural_memory.DSL.effect import matches


def find_by_effect(required: dict) -> list:
    """requires(effect 양식 dict) 를 해소하는 DSL 명세 목록 (body 제외).

    빈 목록이면 막힘 — 호출자가 need.holds 를 따라 하강한다.
    """
    return [spec(name) for name, s in SPECS.items()
            if matches(required, s.get("effect"))]


def find_activatable(need) -> list:
    """find_by_effect 의 Need 래퍼 — need.requires 로 탐색."""
    return find_by_effect(need.requires)
