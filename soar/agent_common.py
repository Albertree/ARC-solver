"""
공통 에이전트 유틸: task dict 기반 WM 구성, 목표 달성 판정, 답 추출.
SOAR 에이전트(ActiveSoarAgent, SoarDemoAgent 등)에서 공유.
"""

from __future__ import annotations

from typing import Any, List

from soar.wm import WorkingMemory


def build_wm_from_task(task: dict) -> WorkingMemory:
    """Task dict (task_id, train, test)로 WM 초기 상태 구성. 출력 결핍을 deficits에 등록."""
    task_id = task.get("task_id", "")
    test = task.get("test", [])
    n_test = len(test)
    deficits: List[Any] = [("GRID", "contents", f"output-test-{i}") for i in range(n_test)]
    if not deficits:
        deficits = [("GRID", "contents", "output-test-0")]

    return WorkingMemory(
        goal=("produce-output", task_id),
        task=task,
        focus="TASK",
        deficits=deficits,
        found={},
        tried=[],
        subgoal=None,
    )


def goal_satisfied(wm: WorkingMemory) -> bool:
    """모든 test 출력이 wm.found에 있으면 True (output_test_0, output_test_1, ...)."""
    n_test = max(1, len((wm.task or {}).get("test", [])))
    return all(f"output_test_{i}" in wm.found for i in range(n_test))


def answers_from_wm(wm: WorkingMemory) -> List[Any]:
    """wm.found에서 output_test_0, output_test_1, ... 순서로 답 리스트 반환. 없으면 None."""
    n_test = max(1, len((wm.task or {}).get("test", [])))
    return [wm.found.get(f"output_test_{i}") for i in range(n_test)]
