"""
GoalStack (모듈 B) — descent 하며 진화하는 목표 스택.

SOAR substate 스택 위에 얹혀, 각 레벨(TASK/PAIR/GRID)의 목표를 보관한다.
목표는 내려갈수록 구체화된다: solve task → make missing grid → determine grid props.
즉 B 는 SOAR substate 스택의 *목표-증강 뷰* — 별도 구조를 두지 않는다.
"""

LEVELS = ["TASK", "PAIR", "GRID", "OBJECT"]


def next_level(level: str):
    """descent 다음 레벨. GRID 가 마지막(Slice 1)."""
    i = LEVELS.index(level)
    return LEVELS[i + 1] if i + 1 < len(LEVELS) else None


class GoalStack:
    """목표 프레임 스택 = SOAR substate 스택 + 레벨/목표 증강."""

    def __init__(self, wm, root_goal: str):
        self.wm = wm
        wm.s1["level"] = "TASK"
        wm.s1["goal"] = root_goal

    def current_level(self) -> str:
        return self.wm.active.get("level")

    def current_goal(self) -> str:
        return self.wm.active.get("goal")

    def descend(self, level: str, goal: str, reason: str) -> bool:
        """막힘 → 한 레벨 intra-descend (SOAR substate push + 목표 프레임)."""
        if not self.wm.push_substate("no-change", "operator"):
            return False
        self.wm.active["level"] = level
        self.wm.active["goal"] = goal
        self.wm.active["descend-reason"] = reason
        return True

    def frames(self) -> list:
        """루트(S1) → 현재까지의 (level, goal, reason) 프레임 목록."""
        out = [{"level": self.wm.s1.get("level"),
                "goal": self.wm.s1.get("goal"), "reason": "(root)"}]
        for sub in self.wm._substate_stack:
            out.append({"level": sub.get("level"), "goal": sub.get("goal"),
                        "reason": sub.get("descend-reason")})
        return out
