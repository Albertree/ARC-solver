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
    SelectTargetOperator,
    CompareOperator,
    ExtractPatternOperator,
    GeneralizeOperator,
    PredictOperator,
    SubmitOperator,
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
        pass

    def propose(self, wm) -> object:
        """[설계 자유] 조건 충족 시 Operator 인스턴스 반환. None 반환 금지."""
        pass


# ── 구체 ProductionRule 구현 — 전부 [설계 자유] ───────────────────────

class SelectTargetRule(ProductionRule):
    """[설계 자유] elaborated["needs_target_selection"] → SelectTargetOperator."""

    def __init__(self):
        super().__init__("rule_select_target")

    def condition(self, wm) -> bool:
        pass

    def propose(self, wm):
        return SelectTargetOperator()


class CompareRule(ProductionRule):
    """[설계 자유] elaborated["has_pending_comparison"] → CompareOperator."""

    def __init__(self):
        super().__init__("rule_compare")

    def condition(self, wm) -> bool:
        pass

    def propose(self, wm):
        return CompareOperator()


class ExtractPatternRule(ProductionRule):
    """[설계 자유] elaborated["ready_for_pattern_extraction"] → ExtractPatternOperator."""

    def __init__(self):
        super().__init__("rule_extract_pattern")

    def condition(self, wm) -> bool:
        pass

    def propose(self, wm):
        return ExtractPatternOperator()


class GeneralizeRule(ProductionRule):
    """[설계 자유] elaborated["ready_for_generalization"] → GeneralizeOperator."""

    def __init__(self):
        super().__init__("rule_generalize")

    def condition(self, wm) -> bool:
        pass

    def propose(self, wm):
        return GeneralizeOperator()


class PredictRule(ProductionRule):
    """[설계 자유] elaborated["ready_for_prediction"] → PredictOperator."""

    def __init__(self):
        super().__init__("rule_predict")

    def condition(self, wm) -> bool:
        pass

    def propose(self, wm):
        return PredictOperator()


class SubmitRule(ProductionRule):
    """[설계 자유] elaborated["all_outputs_found"] → SubmitOperator."""

    def __init__(self):
        super().__init__("rule_submit")

    def condition(self, wm) -> bool:
        pass

    def propose(self, wm):
        return SubmitOperator()


class Proposer:
    """
    [SOAR 강제] 등록된 ProductionRule을 순회해 후보를 수집하는 엔진.
    [설계 자유] 등록할 규칙 목록 (build_proposer에서 결정).
    MUST NOT: 선택(select)이나 적용(apply)을 수행하지 마.
    """

    def __init__(self, rules: list):
        self._rules = rules

    def propose(self, wm) -> list:
        """[SOAR 강제] 발화하는 모든 규칙의 operator 후보 목록 반환."""
        pass


def build_proposer() -> Proposer:
    """[설계 자유] 어떤 ProductionRule을 등록할지. ActiveSoarAgent.solve() 시 생성."""
    rules = [
        SelectTargetRule(),
        CompareRule(),
        ExtractPatternRule(),
        GeneralizeRule(),
        PredictRule(),
        SubmitRule(),
    ]
    return Proposer(rules)
