#!/usr/bin/env python3
"""
SOAR demo in the environment: SOAR WM이 풀이를 이끌어가며, 연산자 적용 시 실제 solver 단계 실행 → WM 갱신.
- WM 결핍 → 연산자 선택 → 효과로 실제 PaG1/비교 등 실행 → found/deficits 갱신. 답은 WM.found 우선, 부족분만 SolverAgent로 보완.
"""

from typing import Any, List, Optional

from arc_env import ARCEnvironment, SolverAgent
from soar import WorkingMemory, run_cycle
from soar.agent_common import build_wm_from_task, goal_satisfied, answers_from_wm


# 테스트할 문제. 예: ["08ed6ac7"], ["easy0004"]
SOLVER_TASK_IDS = ["08ed6ac7"]
VERBOSE = True


def _format_found_value(v: Any) -> str:
    """found 항목 값 요약 (그리드는 크기만)."""
    if v is None:
        return "None"
    if isinstance(v, (list, tuple)):
        if v and isinstance(v[0], (list, tuple)):
            return f"grid {len(v)}x{len(v[0])}"
        return f"list[{len(v)}]"
    if hasattr(v, "view"):
        view = getattr(v, "view", None)
        if isinstance(view, (list, tuple)) and view:
            return f"grid {len(view)}x{len(view[0])}"
    return type(v).__name__


def _format_wme_value(val: Any) -> str:
    """WME value를 한 줄로 요약."""
    if isinstance(val, (list, tuple)) and val and isinstance(val[0], (list, tuple)):
        return "grid %dx%d" % (len(val), len(val[0]))
    if isinstance(val, (list, tuple)) and len(val) > 3:
        return str(val)[:60] + "..."
    return repr(val)[:80]


def _format_wm_triplets(wm: WorkingMemory) -> str:
    """SOAR 스타일 WME 트리플릿 전체: (id ^attr value)."""
    wmes = getattr(wm, "get_all_wmes", None)
    if not callable(wmes):
        return "  (WME 목록 없음)"
    lines = []
    for (id_, attr, val) in wmes():
        lines.append("  (%s ^%s %s)" % (id_, attr, _format_wme_value(val)))
    return "\n".join(lines) if lines else "  (비어 있음)"


def _format_wm_full(wm: WorkingMemory) -> str:
    """WM 전체 내역: 요약 뷰 + WME 트리플릿 목록."""
    lines = [
        "  [요약] goal = %s" % (wm.goal,),
        "         focus = %s" % (wm.focus,),
        "         deficits = %s" % (wm.deficits,),
        "         tried = %s" % (wm.tried,),
        "         subgoal = %s" % (wm.subgoal,),
    ]
    if wm.found:
        found_repr = []
        for k in sorted(wm.found.keys()):
            v = wm.found[k]
            found_repr.append("%s: %s" % (k, _format_found_value(v)))
        lines.append("         found = {%s}" % ", ".join(found_repr))
    else:
        lines.append("         found = {}")
    lines.append("  [WME 트리플릿]")
    lines.append(_format_wm_triplets(wm))
    return "\n".join(lines)


class SoarDemoAgent:
    """
    SOAR가 풀이를 주도: 연산자 적용 시 실제 solver 단계 실행 → WM 갱신.
    답은 WM.found에서 우선 채우고, 빠진 test만 SolverAgent로 보완.
    """

    def __init__(self, verbose: bool = False, soar_max_steps: int = 50):
        self._solver_agent = SolverAgent(verbose=verbose)
        self.verbose = verbose
        self.soar_max_steps = soar_max_steps
        self._last_wm: Optional[WorkingMemory] = None
        self._last_cycle_result: Optional[Any] = None

    def _on_after_apply(self, wm: WorkingMemory, applied: str) -> None:
        """매 WM 변형(연산자 적용) 직후 전체 WM 내역 출력 후 breakpoint()."""
        print("[WM 변형] 연산자 = %r" % (applied,))
        print(_format_wm_full(wm))
        print()
        breakpoint()

    def solve(self, task: dict, step_info: Optional[dict] = None) -> Any:
        """
        1) WM 구성 후 run_cycle 실행 — 연산자 효과로 실제 PaG1 등 실행, WM 갱신.
        2) 답은 WM.found에서 채우고, 빠진 test만 SolverAgent.solve()로 보완 후 반환.
        """
        task_id = task.get("task_id", "")
        if self.verbose:
            print(f"[SoarDemoAgent] task_id={task_id} — SOAR WM 주도 풀이")

        wm = build_wm_from_task(task)
        if self.verbose:
            print("[WM 초기 상태] (run_cycle 진입 전)")
            print(_format_wm_full(wm))
            print()

        result = run_cycle(
            wm,
            max_steps=self.soar_max_steps,
            on_impasse="set_subgoal",
            on_after_apply=self._on_after_apply,
            goal_satisfied=goal_satisfied,
        )

        self._last_wm = wm
        self._last_cycle_result = result

        if self.verbose:
            print(
                f"[SoarDemoAgent] SOAR 완료: applied={result.applied_operator!r} "
                f"impasse={result.impasse} steps={result.steps}"
            )
            print(f"  WM.tried={wm.tried[:8]}{'...' if len(wm.tried) > 8 else ''}")
            print(f"  WM.focus={wm.focus} | found(출력)={[k for k in sorted(wm.found) if k.startswith('output_test_')]}")

        answers = answers_from_wm(wm)
        missing = [i for i, a in enumerate(answers) if a is None]
        if missing:
            fallback = self._solver_agent.solve(task, step_info=step_info)
            if isinstance(fallback, list):
                for i in missing:
                    if i < len(fallback):
                        answers[i] = fallback[i]
            else:
                answers = fallback
        return answers

    def update_memory(self, reward: float) -> None:
        """채점 결과로 메모리 갱신. 필요 시 에피소드 기록 등."""
        if hasattr(self._solver_agent, "update_memory") and callable(self._solver_agent.update_memory):
            self._solver_agent.update_memory(reward)


def main():
    # 풀 문제 목록. None이면 환경이 가진 전체, 리스트면 그만큼만. 개수는 몰라도 됨 — 없을 때까지 푼다.
    task_list = SOLVER_TASK_IDS if SOLVER_TASK_IDS else None
    if task_list is not None:
        print(f"[run_soar_demo] task_list = {task_list} (총 {len(task_list)}개)")
    else:
        print("[run_soar_demo] task_list = None → 환경 전체 문제를 풀 문제가 없을 때까지 실행")
    env = ARCEnvironment(task_list=task_list)

    agent = SoarDemoAgent(verbose=VERBOSE, soar_max_steps=50)

    # 한 문제만 호출하지 않음. get_task → solve → step 반복, task가 없을 때까지 진행 후 스스로 중지.
    result = env.run_benchmark(agent, n=None)
    correct = result["correct"]
    total = result["total"]
    print(f"  correct = {correct} / total = {total}")
    if result.get("results"):
        for r in result["results"][:10]:
            print(f"    {r['task_id']}: reward={r['reward']}, submissions={r['num_submissions']}")
        if total > 10:
            print(f"    ... 외 {total - 10}개")


if __name__ == "__main__":
    main()
