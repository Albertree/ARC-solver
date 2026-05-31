"""
ActiveSoarAgent — 메인 SOAR 에이전트.
ARCEnvironment의 agent.solve(task) 인터페이스를 구현한다.
"""

from agent.wm import WorkingMemory
from agent.descent import descend_to_decisive
from agent.predict import predict, emit_answer
from agent.io import inject_arc_task
from agent.wm_logger import reset_wm_snapshot, print_wm_triplets
from procedural_memory.DSL.library import deposit


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
        ARBOR Slice 1 흐름: inject → 막힘 기반 descent(A) → 결정적 Inter 비교(C) →
        PredictByAllPairCommOp → emit(K). descent 가 SOAR substate(S1→S2→S3 =
        TASK→PAIR→GRID)를 만들고, 결정적 비교에 닿으면 답을 도출·제출한다.

        [설계 자유] max_steps 값. 결정적 비교 없으면 None(미제출) 반환.
        (구 generic operator-dispatch cycle 은 이 흐름에서 미사용 — 스캐폴드로 보존.)
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
            print_wm_triplets(wm, label="After input-link injection", step=0)

        result, _gs = descend_to_decisive(wm, task,
                                          on_level=self._log_descent if self._log_wm else None)

        answers = None
        if result["decisive"]:
            grid = predict(result["evidence"])
            answers = emit_answer(task, grid)
            # anti-unify schema 가 있으면 학습 라이브러리에 적재 (semantic 성장)
            schema = result["evidence"].get("schema")
            if schema is not None:
                deposit(schema, {"task": task_hex}, root=self.semantic_memory_root)

        if self._log_wm:
            print_wm_triplets(wm, label="After descent (substate stack)", step=1)
            print(f"\n[answer] {('제출 ' + str(len(answers)) + '개') if answers else '미제출(결정 불가)'}")

        self._submission_count += 1
        return answers

    @staticmethod
    def _log_descent(level, goal, res):
        """descent 각 레벨 trace 출력 (log_wm 시) — 읽은 ARCKG 정보·비교."""
        print(f"  [{level}] goal: {goal}")
        for line in res["examined"]:
            print(f"        {line}")
        tag = "결정적 ✓ 멈춤" if res["decisive"] else "막힘 → descend"
        print(f"     → {tag}  ({res['reason']})")

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
