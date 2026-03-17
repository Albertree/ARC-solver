"""
active_operators — SOAR Operator 구현체.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SOAR 강제] 각 operator는 precondition + effect 인터페이스를 따른다.
            effect는 반드시 op_status를 success|failure로 설정한다.
            failure → cycle.py가 impasse로 처리.

[설계 자유] 아래 6개 operator의 존재 자체, 이름, precondition 조건, effect 내용.
            비교 함수(compare_fn)와 일반화 함수(generalize_fn)를 외부 주입 가능.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from agent.operators import Operator


class SelectTargetOperator(Operator):
    """
    [설계 자유] 이 operator의 존재, precondition, effect 전부.
    INTENT: wm.comparison_agenda에서 미처리 항목을 꺼내
            wm.pending_comparisons 큐에 옮긴다.
            agenda는 build_wm_from_task()가 초기 항목을 채우고
            impasse 중 deeper analysis 항목이 동적으로 추가된다.
            SelectTargetOperator는 agenda와 relations만 알고,
            항목이 무엇인지(어느 레이어인지)는 알지 못한다.
    MUST NOT: 비교 자체를 수행하지 마 — pending 큐 이동만.
              wm.task를 직접 참조하지 마.
    precondition: elaborated["needs_target_selection"] == True
    """

    def __init__(self):
        super().__init__("select_target")

    def precondition(self, wm) -> bool:
        """[설계 자유]"""
        pass

    def effect(self, wm):
        """
        [설계 자유]
        1. wm.active["comparison_agenda"]에서 relations에 없는 항목 하나 선택
        2. wm.push_pending_comparison(node_a, node_b, context)
        3. agenda에서 해당 항목 제거
        4. op_status = "success" or "failure"
        """
        pass


class CompareOperator(Operator):
    """
    [설계 자유] 이 operator의 존재, precondition, effect 전부.
    INTENT: pending_comparisons 큐에서 한 항목을 꺼내 비교를 수행하고
            결과를 wm.relations에 추가한다.
            비교 함수는 외부 주입(compare_fn) 또는 기본값 사용.
            CompareOperator는 항목이 무엇인지 알지 못한다.
    MUST NOT: 큐에서 여러 항목을 한 번에 처리하지 마 — 1회 = 1 비교.
              특정 비교 라이브러리를 클래스에 하드코딩하지 마.
    precondition: elaborated["has_pending_comparison"] == True
    """

    def __init__(self, compare_fn=None):
        """
        [설계 자유] compare_fn: (node_a, node_b, context) → result.
                   None이면 기본 비교 함수 사용.
        """
        super().__init__("compare")
        self._compare_fn = compare_fn

    def precondition(self, wm) -> bool:
        """[설계 자유]"""
        pass

    def effect(self, wm):
        """
        [설계 자유]
        1. wm.pop_pending_comparison() → {node_a, node_b, context}
        2. self._compare_fn(node_a, node_b, context) 호출
        3. wm.update_dict("relations", key, result) → 새 지식 추가
        4. op_status = "success" or "failure"
        """
        pass


class ExtractPatternOperator(Operator):
    """
    [설계 자유] 이 operator의 존재, precondition, effect 전부.
    INTENT: wm.relations 누적 결과에서 COMM 속성 → wm.invariants,
            DIFF 속성과 방향 → wm.diff_patterns에 추가한다.
            패턴 추출 실패 시 add_dynamic_subgoal()로 deeper analysis 요청.
    MUST NOT: COMM/DIFF 판단 로직을 여기서 구현하지 마 — result의 type 필드 읽기만.
    precondition: elaborated["ready_for_pattern_extraction"] == True
    """

    def __init__(self):
        super().__init__("extract_pattern")

    def precondition(self, wm) -> bool:
        """[설계 자유]"""
        pass

    def effect(self, wm):
        """
        [설계 자유]
        1. wm.relations 순회
        2. COMM → wm.update_dict("invariants", attr, "unchanged")
        3. DIFF  → wm.update_dict("diff_patterns", attr, {type, ...})
        4. op_status = "success" or "failure"
        """
        pass


class GeneralizeOperator(Operator):
    """
    [설계 자유] 이 operator의 존재, precondition, effect 전부.
    INTENT: wm.invariants와 wm.diff_patterns를 일반화 함수에 전달해
            추상 규칙을 생성하고 wm.active_rules에 추가한다.
            일반화 함수와 LTM 저장 함수는 외부 주입 또는 기본값 사용.
    MUST NOT: 특정 일반화 모듈을 클래스에 하드코딩하지 마.
    precondition: elaborated["ready_for_generalization"] == True
    """

    def __init__(self, generalize_fn=None, save_fn=None):
        """
        [설계 자유] generalize_fn: (invariants, diff_patterns) → rule dict.
                   save_fn: rule dict → LTM ref str.
                   None이면 기본 구현 사용.
        """
        super().__init__("generalize")
        self._generalize_fn = generalize_fn
        self._save_fn = save_fn

    def precondition(self, wm) -> bool:
        """[설계 자유]"""
        pass

    def effect(self, wm):
        """
        [설계 자유]
        1. self._generalize_fn(wm.invariants, wm.diff_patterns)
        2. self._save_fn(rule) → LTM ref 경로
        3. wm.active_rules에 {"ref": path, "confidence": ...} 추가
        4. op_status = "success" or "failure"
        """
        pass


class PredictOperator(Operator):
    """
    [설계 자유] 이 operator의 존재, precondition, effect 전부.
    INTENT: wm.active_rules 중 최고 confidence 규칙을 pending test subgoal에 적용해
            출력을 예측하고 wm.mark_subgoal_solved()를 호출한다.
    MUST NOT: 여러 규칙을 병렬로 시도하지 마 — 단일 결정적 예측.
    precondition: elaborated["ready_for_prediction"] == True
    """

    def __init__(self):
        super().__init__("predict")

    def precondition(self, wm) -> bool:
        """[설계 자유]"""
        pass

    def effect(self, wm):
        """
        [설계 자유]
        1. pending test subgoal 하나 선택
        2. wm.active_rules 중 confidence 최고 규칙 선택
        3. 규칙을 test input에 적용 → output 도출
        4. wm.mark_subgoal_solved(test_idx, output)
        5. op_status = "success" or "failure"
        """
        pass


class SubmitOperator(Operator):
    """
    [설계 자유] 이 operator의 존재와 precondition.
    [SOAR 강제] goal_satisfied 조건을 충족시키는 마지막 단계가 있어야 한다.
    INTENT: elaborated["all_outputs_found"] == True이면 op_status = "success" 설정.
    MUST NOT: 실제 채점을 수행하지 마 — ARCEnvironment 책임.
    precondition: elaborated["all_outputs_found"] == True
    """

    def __init__(self):
        super().__init__("submit")

    def precondition(self, wm) -> bool:
        """[설계 자유]"""
        pass

    def effect(self, wm):
        """[설계 자유] op_status = "success" 설정."""
        pass
