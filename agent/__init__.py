"""
agent — ARBOR 에이전트 패키지.

Public interface:
    ActiveSoarAgent   — 메인 에이전트 (유일한 solver, solve 진입점)
    WorkingMemory     — SOAR WM: S1/substate 스택, WME triple
    print_wm_triplets — WM 상태를 SOAR triplet 형식으로 출력

풀이 흐름은 descent(A) → compare(C) → predict 로, agent/{descent,goal_stack,predict}.py
+ procedural_memory/DSL 에 있다. 구 generic operator-dispatch cycle(propose/select/
apply + preference)은 제거됨 — ARBOR 는 preference-search 대신 *연역적 descent* 를 쓴다.
SOAR 의 substate/impasse(막힘→하강) 개념은 WorkingMemory.push_substate 에 남아 있다.
(제거된 코드: git 이력 + wiki soar-manual-reference 에 보존.)
"""

from agent.active_agent import ActiveSoarAgent
from agent.wm import WorkingMemory
from agent.wm_logger import print_wm_triplets

__all__ = ["ActiveSoarAgent", "WorkingMemory", "print_wm_triplets"]
