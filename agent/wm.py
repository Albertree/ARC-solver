"""
WorkingMemory — SOAR 작업 메모리.

SOAR의 4개 구성요소 중 하나.
  WM              ← 현재 문제 상태 전체 (이 파일)
  Production Memory ← elaboration_rules.py + rules.py
  Operators         ← operators.py + active_operators.py
  Cycle             ← cycle.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SOAR 강제] WM은 반드시 존재해야 한다.
            모든 내용은 (identifier, attribute, value) triplet으로 표현된다.
            S1(루트)/S2(서브스테이트) 계층 구조를 가진다.
            S2는 impasse 시 자동 생성, 해결 시 소멸한다.

[설계 자유] WM에 어떤 내용을 담을지 (goal, focus, relations 등 구역 설계)
            S1에 어떤 필드를 둘지
            comparison_agenda / pending_comparisons 같은 탐색 제어 구조
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

MAX_SUBSTATE_DEPTH: int = 2


class WorkingMemory:
    """
    [SOAR 강제] WM 클래스는 반드시 존재해야 한다.
                S1/S2 계층과 triplet 접근 인터페이스(get/set)는 SOAR 프로토콜.
    [설계 자유] S1에 담는 필드 목록과 초기값은 전적으로 설계 선택.
    """

    def __init__(self):
        """
        [설계 자유] 어떤 영역(goal / operator / 탐색제어 / 지식 / 결과)을 S1에 둘지.
        """
        self.s1 = {
            # ── [설계 자유] 목표 영역 ─────────────────────────────────
            "goal": {
                "type": None,
                "subgoals": {},          # {test_0: {status, output?}, ...}
            },
            # ── [SOAR 강제] 연산자 영역 (operator 상태는 WM에 기록된다) ─
            "proposed_ops": [],
            "selected_op":  None,
            "op_status":    "idle",      # idle | running | success | failure
            # ── [설계 자유] 탐색 제어 영역 ───────────────────────────
            "focus": {},                 # {level: str, scope: str}
            "comparison_agenda": [],     # [{node_a, node_b, context}, ...]
            "pending_comparisons": [],   # [{node_a, node_b, context}, ...]
            # ── [설계 자유] 지식 영역 ────────────────────────────────
            "elaborated":    {},         # Elaborator가 매 사이클 채우는 파생 사실
            "relations":     {},         # 비교 결과 누적
            "invariants":    {},         # {attr_path: "unchanged"|"changed"}
            "diff_patterns": {},         # {attr_path: {type, ...}}
            "active_rules":  [],         # [{ref, confidence}, ...]
            # ── [설계 자유] 결과 영역 ────────────────────────────────
            "found": {},                 # {test_0: grid, ...}
        }
        self.task = None                 # [설계 자유] task 참조 (build_wm_from_task가 설정)
        self._substate_stack: list = []  # [SOAR 강제] S2 서브스테이트 스택

    # ------------------------------------------------------------------ #
    # [SOAR 강제] 현재 활성 상태 접근 — S1/S2 계층 구조
    # ------------------------------------------------------------------ #

    @property
    def active(self) -> dict:
        """[SOAR 강제] 현재 활성 상태 (S2 우선, 없으면 S1)."""
        return self._substate_stack[-1] if self._substate_stack else self.s1

    @property
    def depth(self) -> int:
        """[SOAR 강제] 현재 서브스테이트 깊이 (S1=0, S2=1, …)."""
        return len(self._substate_stack)

    # ------------------------------------------------------------------ #
    # [SOAR 강제] WM 값 접근 — triplet 인터페이스
    # ------------------------------------------------------------------ #

    def get(self, key: str):
        """
        [SOAR 강제] WM에서 값을 읽는 인터페이스 (triplet의 value 접근).
        MUST NOT: 여러 value가 있을 때 임의로 하나를 반환하지 마 — get_list() 사용.
        """
        pass

    def set(self, key: str, value):
        """
        [SOAR 강제] WM에 값을 쓰는 인터페이스.
        MUST NOT: goal / found 예약 키를 직접 덮어쓰지 마 — 전용 메서드 사용.
        """
        pass

    def get_list(self, key: str) -> list:
        """[SOAR 강제] WM에서 리스트 값을 읽는 인터페이스. 없으면 빈 리스트."""
        pass

    def update_dict(self, key: str, sub_key: str, value):
        """
        [SOAR 강제] WM dict 필드에 새 항목을 추가하는 인터페이스.
        [설계 자유] 어떤 키(relations / invariants 등)에 무엇을 추가할지.
        """
        pass

    # ------------------------------------------------------------------ #
    # [설계 자유] 목표 영역 헬퍼 — 어떤 subgoal 구조를 쓸지
    # ------------------------------------------------------------------ #

    def init_subgoals(self, test_count: int):
        """
        [설계 자유] test_count 개수만큼 pending subgoal 초기화.
                   goal 구조를 어떻게 정의할지는 설계 선택.
        MUST NOT: 이미 존재하는 subgoal을 덮어쓰지 마.
        """
        pass

    def mark_subgoal_solved(self, test_idx: int, output):
        """[설계 자유] subgoal을 solved로 전환하고 found에 기록."""
        pass

    def add_dynamic_subgoal(self, name: str, description: str):
        """
        [설계 자유] 동적으로 발견된 결핍에 대한 subgoal 추가.
                   어떤 subgoal을 만들지는 설계 선택.
        """
        pass

    # ------------------------------------------------------------------ #
    # [설계 자유] 탐색 제어 헬퍼 — comparison_agenda/pending 구조
    # ------------------------------------------------------------------ #

    def add_to_agenda(self, node_a, node_b, context: dict = None):
        """
        [설계 자유] 비교 예정 항목을 agenda에 추가.
                   agenda 구조 자체가 이 시스템의 설계 선택.
        """
        pass

    def push_pending_comparison(self, node_a, node_b, context: dict = None):
        """[설계 자유] agenda → pending으로 항목 이동 (SelectTargetOperator 호출)."""
        pass

    def pop_pending_comparison(self) -> dict:
        """[설계 자유] pending에서 항목 꺼내기 (CompareOperator 호출)."""
        pass

    # ------------------------------------------------------------------ #
    # [SOAR 강제] 서브스테이트 관리 — impasse 메커니즘
    # ------------------------------------------------------------------ #

    def push_substate(self, subgoal: str, trigger: str) -> bool:
        """
        [SOAR 강제] impasse 발생 시 substate를 생성하는 메커니즘.
                   trigger: "failure" | "no_candidates"
        [설계 자유] subgoal 내용(어떤 목표로 substate를 열지).
        MUST NOT: MAX_SUBSTATE_DEPTH를 초과한 push를 허용하지 마.
        """
        pass

    def pop_substate(self, result=None):
        """
        [SOAR 강제] substate 해결 시 소멸시키는 메커니즘.
        [설계 자유] result를 상위 상태에 어떻게 전달할지.
        """
        pass
