"""
elaboration_rules — SOAR Production Memory의 Elaboration 규칙.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SOAR 강제] Elaborate 단계는 매 사이클 첫 번째로 실행된다.
            Elaborator는 fixed-point까지 반복 적용한다.
            ElaborationRule의 인터페이스(condition → derive)는 SOAR 프로토콜.

[설계 자유] 어떤 파생 사실을 만들지 (규칙 내용 전부).
            파생 사실의 이름과 값.
            Elaborator에 등록할 규칙 목록.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class ElaborationRule:
    """
    [SOAR 강제] Elaboration 규칙의 인터페이스.
               condition(wm) → True 일 때 derive(wm)가 파생 사실 dict를 반환한다.
    [설계 자유] condition의 내용, derive의 내용 (구체 규칙 클래스가 정의).
    MUST NOT: WM을 수정하지 마 — 파생 사실 dict 반환만.
    """

    def __init__(self, name: str):
        self.name = name

    def condition(self, wm) -> bool:
        """[설계 자유] 발화 조건. WM 수정 금지."""
        pass

    def derive(self, wm) -> dict:
        """
        [설계 자유] 파생 사실 dict 반환. 형식: {fact_name: value}
        MUST NOT: 빈 dict 반환 금지.
        """
        pass


class Elaborator:
    """
    [SOAR 강제] ElaborationRule 목록을 fixed-point까지 반복 적용하는 엔진.
               wm.active["elaborated"]를 초기화 후 채운다.
    [설계 자유] 등록할 규칙 목록 (build_elaborator에서 결정).
    MUST NOT: MAX_ITERATIONS 초과 시 강제 종료 (무한 루프 방지).
    """

    MAX_ITERATIONS: int = 20

    def __init__(self, rules: list):
        self._rules = rules

    def run(self, wm):
        """
        [SOAR 강제] fixed-point 반복 엔진 — 사이클마다 호출됨.
        """
        pass


# ------------------------------------------------------------------ #
# 구체 ElaborationRule 구현 — 전부 [설계 자유]
# ------------------------------------------------------------------ #

class NeedsTargetSelectionRule(ElaborationRule):
    """
    [설계 자유] comparison_agenda에 미처리 항목이 있고
               pending_comparisons가 비어있으면
               elaborated["needs_target_selection"] = True 도출.
    """

    def condition(self, wm) -> bool:
        pass

    def derive(self, wm) -> dict:
        return {"needs_target_selection": True}


class HasPendingComparisonRule(ElaborationRule):
    """
    [설계 자유] pending_comparisons 큐에 항목이 있으면
               elaborated["has_pending_comparison"] = True 도출.
    """

    def condition(self, wm) -> bool:
        pass

    def derive(self, wm) -> dict:
        return {"has_pending_comparison": True}


class AllComparisonsDoneRule(ElaborationRule):
    """
    [설계 자유] agenda와 pending이 모두 비어있고
               모든 필수 비교가 relations에 존재하면
               elaborated["all_comparisons_done"] = True 도출.
    """

    def condition(self, wm) -> bool:
        pass

    def derive(self, wm) -> dict:
        return {"all_comparisons_done": True}


class ReadyForPatternExtractionRule(ElaborationRule):
    """
    [설계 자유] all_comparisons_done == True AND
               invariants + diff_patterns 모두 비어있으면
               elaborated["ready_for_pattern_extraction"] = True 도출.
    """

    def condition(self, wm) -> bool:
        pass

    def derive(self, wm) -> dict:
        return {"ready_for_pattern_extraction": True}


class ReadyForGeneralizationRule(ElaborationRule):
    """
    [설계 자유] invariants와 diff_patterns가 모두 채워져 있으면
               elaborated["ready_for_generalization"] = True 도출.
    """

    def condition(self, wm) -> bool:
        pass

    def derive(self, wm) -> dict:
        return {"ready_for_generalization": True}


class ReadyForPredictionRule(ElaborationRule):
    """
    [설계 자유] active_rules가 비어있지 않고
               pending test subgoal이 하나 이상 있으면
               elaborated["ready_for_prediction"] = True 도출.
    """

    def condition(self, wm) -> bool:
        pass

    def derive(self, wm) -> dict:
        return {"ready_for_prediction": True}


class AllOutputsFoundRule(ElaborationRule):
    """
    [설계 자유] 모든 test subgoal이 solved이면
               elaborated["all_outputs_found"] = True 도출.
    """

    def condition(self, wm) -> bool:
        pass

    def derive(self, wm) -> dict:
        return {"all_outputs_found": True}


def build_elaborator() -> Elaborator:
    """
    [설계 자유] 어떤 ElaborationRule을 등록할지.
               ActiveSoarAgent.solve() 호출 시 생성.
    """
    rules = [
        NeedsTargetSelectionRule("needs_target_selection"),
        HasPendingComparisonRule("has_pending_comparison"),
        AllComparisonsDoneRule("all_comparisons_done"),
        ReadyForPatternExtractionRule("ready_for_pattern_extraction"),
        ReadyForGeneralizationRule("ready_for_generalization"),
        ReadyForPredictionRule("ready_for_prediction"),
        AllOutputsFoundRule("all_outputs_found"),
    ]
    return Elaborator(rules)
