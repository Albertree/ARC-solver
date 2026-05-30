"""
agent_common — 답변 추출 공통 유틸.
"""


def answers_from_wm(wm) -> list | None:
    found = wm.active.get("found") or {}
    goal = wm.active.get("goal") or {}
    subs = goal.get("subgoals") or {}
    if not subs:
        return None

    def _test_order(k: str) -> int:
        if k.startswith("test_"):
            try:
                return int(k.split("_", 1)[1])
            except (ValueError, IndexError):
                return 0
        return 0

    keys = sorted(subs.keys(), key=_test_order)
    out = []
    for k in keys:
        out.append(found.get(k))
    if all(v is None for v in out):
        return None
    return out
