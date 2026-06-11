"""
ActiveSoarAgent — 메인 SOAR 에이전트.
ARCEnvironment의 agent.solve(task) 인터페이스를 구현한다.
"""

from agent.wm import WorkingMemory
from agent.decision import run as decision_run
from agent.goal import Goal, deposit_goal
from agent.predict import emit_answer
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
        self._rejected: list = []        # 이 task 에서 "틀림" 으로 돌아온 직전 답들 (reject 누적)
        self._last_answer = None         # 직전 제출한 built-grid (재호출 시 reject 로 이관)

    def solve(self, task, on_step=None) -> list:
        """
        ARBOR SOAR 사이클(decision.run): inject → 루트 목표 → propose/select/apply,
        막히면 impasse→하강. built-grid 가 완성되면 unwind→answer 로 회수해 emit(K).

        retry 구조(SOAR 충실): 환경은 *오답일 때만* 같은 task 를 다시 준다 → solve 가
        같은 task 로 재호출됨 = 직전 답이 "틀림". 그 답을 ``_rejected`` 에 누적해 WM
        (`s1["rejected"]`)에 주입한다. (decision.run 의 *소비*(ranked preference)는 다음
        단계 — 지금은 구조만 완성. → wiki [[arbor]] "SOAR 정렬 정정".)

        [설계 자유] max_steps 값. answer 미도출 시 None(미제출) 반환.
        on_step: decision.run 에 그대로 넘기는 사이클 추적 콜백(visualizer 용).
        """
        task_hex = getattr(task, "task_hex", None)
        if task_hex != self._current_task_hex:        # 새 task → 카운터·reject 초기화
            self._current_task_hex = task_hex
            self._submission_count = 0
            self._rejected = []
            self._last_answer = None
        elif self._last_answer is not None:           # 같은 task 재호출 = 직전 답이 "틀림"
            self._rejected.append(self._last_answer)

        wm = WorkingMemory()
        reset_wm_snapshot(wm)
        if self._log_wm:
            print_wm_triplets(wm, label="Initial WM (before input)", step=0)

        inject_arc_task(task, wm)
        wm.s1["level"] = "TASK"
        deposit_goal(wm, Goal("이 task 를 푼다", scope="TASK"))
        wm.s1["rejected"] = list(self._rejected)      # 틀린 답 누적 → 다음 deliberation 이 회피(예정)
        if self._log_wm:
            print_wm_triplets(wm, label="After input-link injection", step=0)

        decision_run(wm, task, on_step=on_step, max_steps=self._max_steps)

        built = wm.s1.get("answer")
        answers = emit_answer(task, built) if built is not None else None
        self._last_answer = built

        if self._log_wm:
            print_wm_triplets(wm, label="After decision cycle (substate stack)", step=1)
            print(f"\n[answer] {('제출 ' + str(len(answers)) + '개') if answers else '미제출(결정 불가)'}")

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
