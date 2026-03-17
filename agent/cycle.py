"""
cycle — SOAR 결정 사이클.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SOAR 강제] 사이클 순서는 반드시 Elaborate → Propose → Select → Apply.
            Elaborate는 매 사이클 첫 단계 — 생략 불가.
            impasse(후보 없음 / failure) → substate 생성 — 생략 불가.

[설계 자유] max_steps 값
            impasse 시 생성할 subgoal 내용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from agent.wm import MAX_SUBSTATE_DEPTH
from agent.agent_common import goal_satisfied


def run_cycle(wm, elaborator, proposer, max_steps: int = 50) -> dict:
    """
    [SOAR 강제] Elaborate → Propose → Select → Apply 루프 자체.
               goal_satisfied, max_steps, 최상위 impasse까지 반복.
    [설계 자유] max_steps 값, 종료 후 반환 dict의 형태.
    MUST NOT: elaborate 단계를 생략하지 마.
              impasse를 예외로 처리하지 마.
    """
    pass


def _elaborate(wm, elaborator):
    """
    [SOAR 강제] 사이클의 첫 번째 단계. 생략 불가.
               Elaborator를 fixed-point까지 반복 호출해 파생 사실을 WM에 추가.
               Propose가 읽을 WM을 완성시킨다.
    [설계 자유] 어떤 파생 사실을 만들지 (Elaborator/ElaborationRule 내용).
    """
    pass


def _propose(wm, proposer) -> list:
    """
    [SOAR 강제] 사이클의 두 번째 단계.
               Proposer를 호출해 operator 후보 목록을 수집.
               결과를 wm.active["proposed_ops"]에 기록.
    [설계 자유] 어떤 operator를 제안할지 (ProductionRule 내용).
    """
    pass


def _select(candidates: list, wm) -> object:
    """
    [SOAR 강제] 사이클의 세 번째 단계.
               후보 중 하나를 선택해 wm.active["selected_op"]에 기록.
               후보가 없으면 None → _handle_impasse("no_candidates").
    [설계 자유] 선택 기준(PREFERENCE_ORDER 내용).
    """
    pass


def _apply(operator, wm):
    """
    [SOAR 강제] 사이클의 네 번째 단계.
               operator.effect(wm) 호출 → WM에 새 사실 추가 또는 변경.
               완료 후 op_status = "success" | "failure".
    [설계 자유] effect의 내용 (Operator 구현).
    """
    pass


def _handle_impasse(wm, trigger: str) -> bool:
    """
    [SOAR 강제] impasse 메커니즘 — 반드시 substate 생성으로 대응해야 한다.
               trigger: "failure" (op 실패) | "no_candidates" (후보 없음).
               push_substate 성공 → True (사이클 계속).
               push_substate 실패 (depth >= MAX) → False (해결 불가, 종료).
    [설계 자유] substate에 어떤 subgoal을 넣을지.
    MUST NOT: impasse를 예외로 처리하지 마.
    """
    pass
