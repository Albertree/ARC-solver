"""
rules — SOAR Production Memory의 Propose 규칙.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SOAR 강제] ProductionRule의 인터페이스(condition + propose).
            Proposer는 모든 규칙을 순회해 후보를 수집하는 엔진.

[설계 자유] 어떤 WM 상태에서 어떤 operator를 제안할지 (규칙 내용 전부).
            condition의 조건, propose가 반환하는 operator.
            Proposer에 등록할 규칙 목록.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from agent.active_operators import (
    SolveTaskOperator,
    SelectTargetOperator,
    CompareOperator,
    ExtractPatternOperator,
    GeneralizeOperator,
    DescendOperator,
    PredictOperator,
    SubmitOperator,
    VerifyOperator,
)


class ProductionRule:
    """
    [SOAR 강제] Production Rule 인터페이스. condition + propose.
    [설계 자유] condition 내용, propose가 반환하는 operator.
    MUST NOT: condition에서 WM을 수정하지 마.
              condition에서 elaborated 이외를 직접 계산하지 마.
              propose에서 operator를 실행하지 마.
    """

    def __init__(self, name: str):
        self.name = name

    def condition(self, wm) -> bool:
        """[설계 자유] elaborated facts만 읽어 발화 조건 판단."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.condition() must be implemented."
        )

    def propose(self, wm) -> object:
        """[설계 자유] 조건 충족 시 Operator 인스턴스 반환. None 반환 금지."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.propose() must be implemented."
        )


# ── 구체 ProductionRule 구현 — 전부 [설계 자유] ───────────────────────


class SolveTaskRule(ProductionRule):
    """
    S1에 ^current-task가 있고 아직 ^operator가 없을 때 solve-task를 제안한다.
    """

    def __init__(self):
        super().__init__("rule_solve_task")

    def condition(self, wm) -> bool:
        state = wm.s1
        return bool(state.get("current-task")) and "operator" not in state

    def propose(self, wm):
        return SolveTaskOperator()


class SelectTargetRule(ProductionRule):
    """needs_target_selection == True → SelectTargetOperator."""

    def __init__(self):
        super().__init__("rule_select_target")

    def condition(self, wm) -> bool:
        return wm.active.get("needs_target_selection") is True

    def propose(self, wm):
        return SelectTargetOperator()


class CompareRule(ProductionRule):
    """has_pending_comparison OR (all_comparisons_done AND no matching) → CompareOperator."""

    def __init__(self):
        super().__init__("rule_compare")

    def condition(self, wm) -> bool:
        state = wm.active
        if state.get("has_pending_comparison") is True:
            return True
        if (state.get("all_comparisons_done") is True
                and state.get("matching-results") is None):
            return True
        return False

    def propose(self, wm):
        return CompareOperator()


class ExtractPatternRule(ProductionRule):
    """ready_for_pattern_extraction == True → ExtractPatternOperator."""

    def __init__(self):
        super().__init__("rule_extract_pattern")

    def condition(self, wm) -> bool:
        return wm.active.get("ready_for_pattern_extraction") is True

    def propose(self, wm):
        return ExtractPatternOperator()


class GeneralizeRule(ProductionRule):
    """[설계 자유] elaborated["ready_for_generalization"] → GeneralizeOperator."""

    def __init__(self):
        super().__init__("rule_generalize")

    def condition(self, wm) -> bool:
        raise NotImplementedError("GeneralizeRule.condition() not implemented.")

    def propose(self, wm):
        return GeneralizeOperator()


class PredictRule(ProductionRule):
    """[설계 자유] elaborated["ready_for_prediction"] → PredictOperator."""

    def __init__(self):
        super().__init__("rule_predict")

    def condition(self, wm) -> bool:
        raise NotImplementedError("PredictRule.condition() not implemented.")

    def propose(self, wm):
        return PredictOperator()


class SubmitRule(ProductionRule):
    """[설계 자유] elaborated["all_outputs_found"] → SubmitOperator."""

    def __init__(self):
        super().__init__("rule_submit")

    def condition(self, wm) -> bool:
        raise NotImplementedError("SubmitRule.condition() not implemented.")

    def propose(self, wm):
        return SubmitOperator()


class VerifyRule(ProductionRule):
    """
    [설계 자유] verify 연산을 위한 ProductionRule.

    인지 수준의 verify(predicted_output, constraints)에 대응하며,
    elaborated["all_outputs_found"]와 같은 고수준 제약 판단이 끝났을 때
    VerifyOperator를 제안한다.

    기본 설계에서는 SubmitRule과 동일한 발화 조건을 사용하지만,
    필요하다면 나중에 제약 검사를 더 세분화할 수 있다.
    """

    def __init__(self):
        super().__init__("rule_verify")

    def condition(self, wm) -> bool:
        """[설계 자유] 현재는 SubmitRule과 동일한 플래그 사용을 가정."""
        raise NotImplementedError("VerifyRule.condition() not implemented.")

    def propose(self, wm):
        return VerifyOperator()


class Proposer:
    """
    [SOAR 강제] 등록된 ProductionRule을 순회해 후보를 수집하는 엔진.
    [설계 자유] 등록할 규칙 목록 (build_proposer에서 결정).
    MUST NOT: 선택(select)이나 적용(apply)을 수행하지 마.
    """

    def __init__(self, rules: list):
        self._rules = rules

    def propose(self, wm) -> list:
        """발화한 규칙이 낸 오퍼레이터 인스턴스 목록. NotImplemented 규칙은 건너뜀."""
        candidates: list = []
        for rule in self._rules:
            try:
                if not rule.condition(wm):
                    continue
                op = rule.propose(wm)
            except NotImplementedError:
                continue
            if op is not None:
                candidates.append(op)
        return candidates


def build_proposer() -> Proposer:
    """[설계 자유] 어떤 ProductionRule을 등록할지. ActiveSoarAgent.solve() 시 생성."""
    rules = [
        # SolveTaskRule은 추상 오퍼레이터이므로 직접 사이클에서 구체 operator가 동작한다.
        # compare: SelectTarget + Compare
        SelectTargetRule(),
        CompareRule(),
        # collect
        ExtractPatternRule(),
        # generalize
        GeneralizeRule(),
        # descend (DescendRule는 elaboration 설계 이후 추가 예정)
        # predict
        PredictRule(),
        # verify
        SubmitRule(),
        VerifyRule(),
    ]
    return Proposer(rules)
