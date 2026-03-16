"""
Active SOAR Agent: deficit-driven exploration using component-in/between analysis and 0/1/2-order relations.
결핍 주도 탐색 + 컴포넌트 내부/간 분석 + 0·1·2차 관계를 SOAR 사이클로 수행하는 에이전트.
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional

from soar.wm import WorkingMemory
from soar.cycle import run_cycle
from soar.rules import Proposer, ProductionRule
from soar.active_operators import merged_operators
from soar.agent_common import build_wm_from_task, goal_satisfied, answers_from_wm


def active_proposer() -> Proposer:
    """Proposer with rules for both base OPERATORS and ACTIVE_OPERATORS (merged)."""
    merged = merged_operators()
    rules = [ProductionRule(spec.precondition, name) for name, spec in merged.items()]
    return Proposer(rules=rules)


# 선호도: 관계 결핍 → 분석 → (G0 vs G1 결론 추출) → 같은 그리드 내 객체 비교 → DIFF 깊이 분석 → invariant 예측 → 탐색 → 제출
PREFERENCE_ORDER_ACTIVE: List[str] = [
    "add-relation-deficits",
    "analyze-inside",
    "analyze-between",
    "extract-grid-property-conclusions",
    "create-relation-0",
    "create-relation-1",
    "create-relation-2",
    "compare-objects-within-grid",
    "deepen-diff-ordering",
    "predict-from-invariant",
    "set-exploration-target",
    "explore",
    "submit-answer",
]


def select_operator_active(
    wm: WorkingMemory,
    candidates: List[str],
    preference_order: Optional[List[str]] = None,
) -> Optional[str]:
    """Select one operator using active preference order (relation/explore before submit)."""
    order = preference_order or PREFERENCE_ORDER_ACTIVE
    if not candidates:
        return None
    for name in order:
        if name in candidates:
            return name
    return candidates[0]


class ActiveSoarAgent:
    """
    SOAR 구조를 따르는 능동 탐색 에이전트.
    - 결핍: 출력 그리드(contents) + 선택적으로 RELATION 0/1/2 결핍.
    - 연산자: add-relation-deficits, analyze-inside, analyze-between, create-relation-0/1/2, set-exploration-target, explore, submit-answer.
    - Decision cycle: propose → select (active preference) → apply → WM 갱신. Impasse 시 subgoal(S2) 한 번 더 시도.
    """

    def __init__(
        self,
        verbose: bool = False,
        max_steps: int = 150,
        use_solver_fallback: bool = True,
    ):
        self.verbose = verbose
        self.max_steps = max_steps
        self.use_solver_fallback = use_solver_fallback
        self._solver_agent = None
        if use_solver_fallback:
            try:
                from arc_env import SolverAgent
                self._solver_agent = SolverAgent(verbose=verbose)
            except Exception:
                self._solver_agent = None
        self._last_wm: Optional[WorkingMemory] = None
        self._last_result: Optional[Any] = None

    def solve(self, task: dict, step_info: Optional[dict] = None) -> Any:
        """
        1) WM 구성 후 run_cycle 실행 (merged operators + active preference).
        2) 답은 WM.found에서 채우고, 빠진 test는 SolverAgent로 보완 (use_solver_fallback 시).
        """
        task_id = task.get("task_id", "")
        if self.verbose:
            print(f"[ActiveSoarAgent] task_id={task_id} — 능동 탐색 (relation/explore/submit)")

        wm = build_wm_from_task(task)
        operators = merged_operators()
        proposer = active_proposer()
        result = run_cycle(
            wm,
            proposer=proposer,
            select_fn=lambda wm, cand: select_operator_active(wm, cand),
            operators=operators,
            max_steps=self.max_steps,
            on_impasse="set_subgoal",
            goal_satisfied=goal_satisfied,
        )

        self._last_wm = wm
        self._last_result = result

        if self.verbose:
            print(
                f"[ActiveSoarAgent] 완료: applied={result.applied_operator!r} "
                f"impasse={result.impasse} steps={result.steps}"
            )
            print(f"  deficits(남은)={len(wm.deficits)} tried={wm.tried[:6]}...")
            rk = [k for k in sorted(wm.found) if k.startswith("relation_")]
            if rk:
                print(f"  relation found: {rk[:8]}{'...' if len(rk) > 8 else ''}")

        answers = answers_from_wm(wm)
        missing = [i for i, a in enumerate(answers) if a is None]
        if missing and self._solver_agent:
            fallback = self._solver_agent.solve(task, step_info=step_info)
            if isinstance(fallback, list):
                for i in missing:
                    if i < len(fallback):
                        answers[i] = fallback[i]
            else:
                answers = fallback
        return answers

    def update_memory(self, reward: float) -> None:
        if self._solver_agent and hasattr(self._solver_agent, "update_memory"):
            self._solver_agent.update_memory(reward)
