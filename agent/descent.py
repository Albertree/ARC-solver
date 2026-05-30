"""
Descent (모듈 A = intra) — 막혀야 내려간다 (P1: 계층 깊이는 *필요* 에 의해).

TASK→PAIR→GRID. 각 레벨에서 Inter 비교(모듈 C)를 시도하고, 목적 달성이 불가능하면
(막힘) 다음 레벨로 intra-descend 한다. 강제 하강 ✗ — 결정적 비교를 찾는 순간 멈춘다.

비교 자체는 모듈 C(relation), 목표 스택은 모듈 B(GoalStack). A 는 *언제 내려갈지* 만 정한다.
"""

from procedural_memory.DSL.util import pairs_of, role_of
from procedural_memory.DSL.property import size, color, contents
from procedural_memory.DSL.relation import select, compare_set, verdict
from agent.goal_stack import GoalStack, next_level

# 레벨별 목표 (B 가 descent 시 채택) — 내려갈수록 구체화
_GOAL = {
    "TASK": "solve task — Pa 의 출력 만들기",
    "PAIR": "Pa 에 빠진 grid(출력) 만들기",
    "GRID": "출력 grid 의 {size, color, contents} 정하기",
}

_is_output = lambda g: role_of(g) == "output"


def _try_resolve(level: str, task) -> dict:
    """현재 레벨에서 결정적 비교를 시도한다.
    반환: {decisive, reason, receipts, evidence}. decisive=False 면 막힘."""
    if level == "TASK":
        # 형제 TASK 가 없으니 비교 0 (P1: 자연 skip) → 결정 불가
        return {"decisive": False, "reason": "형제 TASK 없음 → 비교 0",
                "receipts": [], "evidence": None}

    if level == "PAIR":
        # pair 끼리 Inter 비교 — pair property(grid-count)뿐, 출력 내용은 못 정함
        receipts = compare_set(select(task, "pair"))
        return {"decisive": False,
                "reason": "pair 비교는 grid-count 뿐 → 출력 grid 내용 미정",
                "receipts": receipts, "evidence": None}

    if level == "GRID":
        # 다른 pair 의 출력 grid(role==G1)끼리 Inter 비교 — Pa.G1 은 가려져 자연 제외
        g1s = [g for p in pairs_of(task) for g in select(p, "grid", _is_output)]
        receipts = compare_set(g1s)
        all_comm = bool(receipts) and all(verdict(r)[0] == "COMM" for _, _, r in receipts)
        evidence = None
        if all_comm:
            ref = g1s[0]  # 전부 COMM → 공통값 = 아무 example G1
            evidence = {"size": size(ref), "color": color(ref), "contents": contents(ref)}
        reason = ("모든 example G1 COMM → 공통 grid 가 답" if all_comm
                  else "G1 들이 COMM 아님 → 결정 불가")
        return {"decisive": all_comm, "reason": reason,
                "receipts": receipts, "evidence": evidence}

    return {"decisive": False, "reason": f"미지원 level {level}",
            "receipts": [], "evidence": None}


def descend_to_decisive(wm, task, on_level=None):
    """막힘 기반 descent 루프. 결정적 비교에 도달하면 (result, goal_stack) 반환.

    on_level(level, goal, result): 각 레벨 방문 시 콜백 (로그·해석용).
    """
    gs = GoalStack(wm, _GOAL["TASK"])
    while True:
        level = gs.current_level()
        result = _try_resolve(level, task)
        if on_level:
            on_level(level, gs.current_goal(), result)
        if result["decisive"]:
            return result, gs
        nxt = next_level(level)
        if nxt is None:
            return result, gs  # 더 못 내려감 (Slice 1 범위에선 미발생)
        gs.descend(nxt, _GOAL[nxt], result["reason"])
