"""
ActiveSoarAgent — 메인 SOAR 에이전트.
ARCEnvironment의 agent.solve(task) 인터페이스를 구현한다.
"""

from agent.wm import WorkingMemory
from agent.cycle import run_cycle
from agent.elaboration_rules import build_elaborator
from agent.rules import build_proposer
from agent.memory import load_rules_from_ltm
from agent.agent_common import answers_from_wm
from agent.io import inject_arc_task
from agent.wm_logger import reset_wm_snapshot, print_wm_triplets


class ActiveSoarAgent:
    """
    [SOAR 강제] SOAR 사이클을 실행하는 에이전트 래퍼가 있어야 한다.
    [설계 자유] solve() 호출 횟수 제한(can_retry), LTM 로드 방식,
               chunking 콜백 연결 방식.
    MUST NOT: ARCSolver 등 별도 solver를 fallback으로 사용하지 마.
              solve() 1회 = 1 제출.
    """

    def __init__(
        self,
        semantic_memory_root: str = "semantic_memory",
        episodic_memory_root: str = "episodic_memory",
        procedural_memory_root: str = "procedural_memory",
        max_steps: int = 50,
        log_wm: bool = False,
    ):
        """[설계 자유] memory 루트 경로 3개, 사이클 파라미터, 제출 횟수 카운터."""
        self.semantic_memory_root = semantic_memory_root
        self.episodic_memory_root = episodic_memory_root
        self.procedural_memory_root = procedural_memory_root
        self._max_steps = max_steps
        self._log_wm = log_wm
        self._submission_count: int = 0
        self._current_task_hex: str = None

    def solve(self, task) -> list:
        """
        [SOAR 강제] 사이클 실행 흐름 (WM 초기화 → run_cycle → 결과 추출) 자체.
        [설계 자유] LTM rule 선로드 방식, max_steps 값.

        흐름:
          1. 새 태스크이면 _submission_count 리셋
          2. WorkingMemory 생성 후 reset_wm_snapshot() 호출
          3. log_wm 활성 시 "Initial WM (before input)" 출력
          4. inject_arc_task(task, wm) — input-link에 task_hex 주입
          5. log_wm 활성 시 "After input-link injection" 출력
          6. LTM rule 로드 → wm.s1["active_rules"] 초기화
          7. elaborator = build_elaborator()
          8. proposer   = build_proposer()
          9. run_cycle(wm, elaborator, proposer, max_steps, stop_on_goal=True)
          10. log_wm 활성 시 [cycle] 요약 출력
          11. answers = answers_from_wm(wm)
          12. _submission_count += 1
          13. return answers
        """
        task_hex = getattr(task, "task_hex", None)
        if task_hex != self._current_task_hex:
            self._current_task_hex = task_hex
            self._submission_count = 0

        wm = WorkingMemory()
        reset_wm_snapshot(wm)

        if self._log_wm:
            print_wm_triplets(wm, label="Initial WM (before input)", step=0)

        inject_arc_task(task, wm)

        if self._log_wm:
            print_wm_triplets(wm, label="After input-link injection (before cycle)", step=0)

        try:
            rules = load_rules_from_ltm(task_hex, self.semantic_memory_root)
        except NotImplementedError:
            rules = []
        wm.s1["active_rules"] = rules

        elaborator = build_elaborator()
        proposer = build_proposer()
        out = run_cycle(
            wm,
            elaborator,
            proposer,
            max_steps=self._max_steps,
            stop_on_goal=True,
            log_wm=self._log_wm,
        )

        if self._log_wm:
            print(f"\n[cycle] {out}")

        answers = answers_from_wm(wm)
        self._submission_count += 1
        return answers

    def on_substate_resolved(self, substate: dict, task_hex: str):
        """
        [SOAR 강제] subgoal 해결 시 chunking 트리거.
        [설계 자유] chunk 결과를 어떻게 저장할지.
        MUST NOT: solve 루프 내부에서 직접 호출하지 마 — cycle.py가 호출.
        """
        raise NotImplementedError("ActiveSoarAgent.on_substate_resolved() not implemented.")

    @property
    def can_retry(self) -> bool:
        """[설계 자유] 최대 제출 횟수 (현재 3회). 태스크별 카운터."""
        return self._submission_count < 3
