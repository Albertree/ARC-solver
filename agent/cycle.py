"""
cycle — SOAR 결정 사이클.

━━━━━━━━━━━━━━━━━━━━━━━━��━━━━━━━━━━━━━━━
[SOAR 강제] 사이클 순서는 반드시 Elaborate → Propose → Select → Apply.
            Elaborate는 매 사이클 첫 단계 — 생략 불가.
            impasse(후보 없음 / failure) → substate 생성 — 생략 불가.

[설계 자유] max_steps 값
            impasse 시 생성할 subgoal 내용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━��━━━━━━━━
"""

from __future__ import annotations

from agent.agent_common import goal_satisfied
from agent.wm_logger import print_wm_triplets
from agent.propose_wm import (
    materialize_operator_proposals,
    mark_operator_selected,
    clear_s1_operator_slots,
)
from agent.preferences import select_operator


def run_cycle(
    wm,
    elaborator,
    proposer,
    max_steps: int = 50,
    *,
    stop_on_goal: bool = True,
    log_wm: bool = True,
    trace_logger=None,
) -> dict:
    """
    Elaborate → Propose → Select → Apply 루프.

    trace_logger: TraceLogger 인스턴스. None이면 기존 동작(터미널만 출력).
    """
    step = 0
    while step < max_steps:
        if stop_on_goal and _s1_goal_satisfied(wm):
            break

        # WME 스냅샷: 사이클 시작 시점
        wme_before = len(wm.wme_records)

        _elaborate(wm, elaborator)
        if log_wm and trace_logger is None:
            print_wm_triplets(wm, label="After: elaborate", step=step)

        candidates = _propose(wm, proposer)
        if log_wm and trace_logger is None:
            print_wm_triplets(wm, label="After: propose", step=step)

        selected = _select(candidates, wm)
        if log_wm and trace_logger is None:
            print_wm_triplets(wm, label="After: select", step=step)

        if selected is None:
            cont = _handle_impasse(wm, "no_candidates")
            if log_wm and trace_logger is None:
                print_wm_triplets(
                    wm, label="After: impasse(no_candidates)", step=step
                )
            if trace_logger:
                trace_logger.begin_cycle(step + 1, "(no candidates)")
                trace_logger.write_wm_changes(wm.wme_records, wme_before)
                trace_logger.write_interpretation({
                    "action": "후보 operator가 없어 impasse 발생",
                    "meaning": "현재 WM 상태에서 적용 가능한 operator가 없음",
                    "reason": "모든 proposal rule의 condition이 False",
                    "storage": "WM 변화 없음",
                })
            if not cont:
                break
            step += 1
            continue

        apply_outcome, interpretation = _apply(selected, wm)

        if log_wm and trace_logger is None:
            print_wm_triplets(
                wm,
                label=f"After: apply({selected.name})",
                step=step,
            )

        # trace logger: 사이클 블록 출력
        if trace_logger:
            trace_logger.begin_cycle(step + 1, selected.name)
            trace_logger.write_wm_changes(wm.wme_records, wme_before)
            trace_logger.write_interpretation(interpretation)

        if apply_outcome == "failure":
            cont = _handle_impasse(wm, "failure")
            if log_wm and trace_logger is None:
                print_wm_triplets(wm, label="After: impasse(failure)", step=step)
            if not cont:
                break
        elif wm.depth == 0 and apply_outcome == "no_change":
            ok = wm.push_substate("no-change", "operator")
            if log_wm and trace_logger is None:
                print_wm_triplets(
                    wm, label="After: impasse(no-change)", step=step
                )
            if not ok:
                break

        step += 1

    return {
        "steps_taken": step,
        "goal_satisfied": bool(_s1_goal_satisfied(wm)),
    }


def _s1_goal_satisfied(wm) -> bool:
    """서브스테이트에 있어도 S1의 goal만 본다."""
    goal = wm.s1.get("goal")
    if goal is None:
        return False
    subs = goal.get("subgoals") or {}
    if not subs:
        return True
    for _k, sg in sorted(subs.items()):
        if not isinstance(sg, dict):
            continue
        if sg.get("status") != "solved":
            return False
    return True


def _operator_id_for_name(state: dict, name: str) -> str | None:
    for k, v in state.items():
        if (
            len(k) > 1
            and k[0] == "O"
            and k[1:].isdigit()
            and isinstance(v, dict)
            and v.get("name") == name
        ):
            return k
    return None


def _elaborate(wm, elaborator) -> None:
    elaborator.run(wm)


def _propose(wm, proposer) -> list:
    candidates = proposer.propose(wm) or []
    if wm.depth == 0 and candidates:
        materialize_operator_proposals(wm, candidates)
    return candidates


def _select(candidates: list, wm):
    sel = select_operator(candidates, wm)
    if sel is None:
        return None
    if wm.depth == 0:
        oid = _operator_id_for_name(wm.s1, sel.name)
        if oid:
            wm.s1["operator"] = oid
        mark_operator_selected(wm)
    return sel


def _apply(operator, wm) -> tuple[str, dict | None]:
    """
    operator.effect(wm)를 호출한다.

    반환값: (outcome, interpretation)
        outcome: "failure" | "no_change" | "changed"
        interpretation: operator가 반환한 해석 dict (또는 None)
    """
    n_before = len(wm.wme_records)
    try:
        interpretation = operator.effect(wm)
    except Exception:
        return "failure", None
    n_after = len(wm.wme_records)
    if n_after == n_before:
        return "no_change", interpretation
    return "changed", interpretation


def _handle_impasse(wm, trigger: str) -> bool:
    """
    True: 사이클 계속. False: 종료(깊이 한계 또는 최상위에서 후보 없음).
    """
    if trigger == "no_candidates":
        if wm.depth > 0:
            wm.pop_substate()
            clear_s1_operator_slots(wm)
            return True
        return False

    if trigger == "failure":
        if wm.push_substate("constraint-failure", "operator"):
            return True
        return False

    return False
