"""
Preference: SOAR 연산자 선택 투표에 해당.
- Propose된 후보 중 하나를 선택. 선호도 순서로 해석 (첫 번째 일치 = Best).
- SOAR: + Acceptable, > Best, ~ Prohibit 등. 여기서는 고정 순서로 Best 우선.
- select_operator(wm, candidates) -> str | None (None = impasse).
"""

from __future__ import annotations

from typing import List, Optional

from soar.wm import WorkingMemory


# SOAR preference: 목록 순서 = 선호도 (앞일수록 Best). 첫 번째로 제안된 후보가 선택됨.
PREFERENCE_ORDER: List[str] = [
    "submit-answer",
    "explore",
    "set-exploration-target",
]


def select_operator(
    wm: WorkingMemory,
    candidates: List[str],
    preference_order: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Select one operator from candidates. Uses preference_order (default PREFERENCE_ORDER):
    first candidate that appears in the order list wins. If no candidates, return None (impasse).
    """
    order = preference_order if preference_order is not None else PREFERENCE_ORDER
    if not candidates:
        return None
    for name in order:
        if name in candidates:
            return name
    return candidates[0]
