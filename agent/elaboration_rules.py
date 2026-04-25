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

    # i_support = True → 조건이 거짓이 되면 파생 사실을 자동 철회
    i_support: bool = False

    def __init__(self, name: str):
        self.name = name

    def condition(self, wm) -> bool:
        """[설계 자유] 발화 조건. WM 수정 금지."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.condition() must be implemented."
        )

    def derive(self, wm) -> dict:
        """
        [설계 자유] 파생 사실 dict 반환. 형식: {fact_name: value}
        MUST NOT: 빈 dict 반환 금지.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.derive() must be implemented."
        )


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
        i-support: 조건이 거짓이 되면 파생 사실을 자동 철회한다.
        """
        iterations = 0
        while iterations < self.MAX_ITERATIONS:
            iterations += 1
            changed = False

            state = wm.active

            # --- i-support 스타일 처리: input-link에 task가 없어지면
            #     해당 지원을 받던 current-task도 자동 제거한다. ---
            io = state.get("io") or {}
            in_link = io.get("input-link") or {}
            if "task" not in in_link and "current-task" in state:
                del state["current-task"]
                changed = True

            # --- 각 규칙 적용 (파생 사실 추가/갱신 + i-support 철회) ---
            for rule in self._rules:
                try:
                    cond = rule.condition(wm)
                except NotImplementedError:
                    continue

                if cond:
                    try:
                        delta = rule.derive(wm)
                    except NotImplementedError:
                        continue
                    if not delta:
                        continue
                    for key, value in delta.items():
                        if key in state and state[key] == value:
                            continue
                        state[key] = value
                        changed = True
                else:
                    # i-support 철회: 조건이 거짓이면 파생 사실 제거
                    if not getattr(rule, "i_support", False):
                        continue
                    try:
                        delta = rule.derive(wm)
                    except NotImplementedError:
                        continue
                    if not delta:
                        continue
                    for key in delta:
                        if key in state:
                            del state[key]
                            changed = True

            if not changed:
                break


# ------------------------------------------------------------------ #
# 구체 ElaborationRule 구현 — 전부 [설계 자유]
# ------------------------------------------------------------------ #


class InputTaskToStateRule(ElaborationRule):
    """
    SOAR 규칙:
      sp { elaborate*input*task
        (state <s> ^io.input-link <in>)
        (<in> ^task <t>)
      -->
        (<s> ^current-task <t>)
      }

    이 구현에서는:
      - wm.s1['io']['input-link']['task'] 가 존재하고
      - wm.s1 에 아직 'current-task' 슬롯이 없을 때
        derive(wm) 가 {"current-task": <task_dict>} 를 반환한다고 해석한다.

    실제 WM에 붙이는 방식은 Elaborator.run 구현에서 결정한다.
    (예: wm.active.update(derive_dict))
    """

    def condition(self, wm) -> bool:
        state = wm.active
        io = state.get("io") or {}
        in_link = io.get("input-link") or {}
        has_task = "task" in in_link
        has_current = "current-task" in state
        return bool(has_task and not has_current)

    def derive(self, wm) -> dict:
        state = wm.active
        io = state.get("io") or {}
        in_link = io.get("input-link") or {}
        task_val = in_link.get("task")
        if task_val is None:
            # condition이 True일 때만 호출된다는 가정이지만, 방어적으로 처리.
            return {}
        return {"current-task": task_val}

class NeedsTargetSelectionRule(ElaborationRule):
    """
    current-task가 있고, 아직 pending-compare가 설정되지 않았고,
    active_rules도 없으면 needs_target_selection = True를 도출한다.
    (active_rules가 이미 있으면 분석 단계를 건너뛴다.)
    """
    i_support = True

    def condition(self, wm) -> bool:
        state = wm.active
        has_task = bool(state.get("current-task"))
        no_pending = state.get("pending-compare") is None
        no_rules = not state.get("active_rules")
        return has_task and no_pending and no_rules

    def derive(self, wm) -> dict:
        return {"needs_target_selection": True}


class HasPendingComparisonRule(ElaborationRule):
    """
    pending-compare 리스트에 항목이 있으면
    has_pending_comparison = True를 도출한다.
    """
    i_support = True

    def condition(self, wm) -> bool:
        state = wm.active
        pending = state.get("pending-compare")
        return isinstance(pending, list) and len(pending) > 0

    def derive(self, wm) -> dict:
        return {"has_pending_comparison": True}


class AllComparisonsDoneRule(ElaborationRule):
    """
    pending-compare가 빈 리스트이고 compare-results가 있으면
    all_comparisons_done = True를 도출한다.
    """
    i_support = True

    def condition(self, wm) -> bool:
        state = wm.active
        pending = state.get("pending-compare")
        results = state.get("compare-results")
        return (
            isinstance(pending, list) and len(pending) == 0
            and isinstance(results, list) and len(results) > 0
        )

    def derive(self, wm) -> dict:
        return {"all_comparisons_done": True}


class ReadyForPatternExtractionRule(ElaborationRule):
    """
    matching-results가 있고 아직 invariants가 없으면
    ready_for_pattern_extraction = True를 도출한다.
    """
    i_support = True

    def condition(self, wm) -> bool:
        state = wm.active
        has_matching = state.get("matching-results") is not None
        no_invariants = state.get("invariants") is None
        return has_matching and no_invariants

    def derive(self, wm) -> dict:
        return {"ready_for_pattern_extraction": True}


class ReadyForGeneralizationRule(ElaborationRule):
    """
    invariants와 transform-targets가 모두 채워져 있고
    아직 active_rules가 없으면 ready_for_generalization = True 도출.
    """
    i_support = True

    def condition(self, wm) -> bool:
        state = wm.active
        has_inv = isinstance(state.get("invariants"), list)
        has_tf = isinstance(state.get("transform-targets"), list)
        no_rules = state.get("active_rules") is None
        return has_inv and has_tf and no_rules

    def derive(self, wm) -> dict:
        return {"ready_for_generalization": True}


class ReadyForPredictionRule(ElaborationRule):
    """
    active_rules가 비어있지 않고 pending test subgoal이 하나 이상 있으면
    ready_for_prediction = True를 도출한다.
    """
    i_support = True

    def condition(self, wm) -> bool:
        state = wm.active
        rules = state.get("active_rules")
        if not isinstance(rules, list) or len(rules) == 0:
            return False
        goal = state.get("goal") or {}
        subgoals = goal.get("subgoals") or {}
        for sg in subgoals.values():
            if isinstance(sg, dict) and sg.get("status") == "pending":
                return True
        return False

    def derive(self, wm) -> dict:
        return {"ready_for_prediction": True}


class AllOutputsFoundRule(ElaborationRule):
    """
    모든 test subgoal이 solved이면 all_outputs_found = True 도출.
    """
    i_support = True

    def condition(self, wm) -> bool:
        state = wm.active
        goal = state.get("goal") or {}
        subgoals = goal.get("subgoals") or {}
        if not subgoals:
            return False
        for sg in subgoals.values():
            if isinstance(sg, dict) and sg.get("status") != "solved":
                return False
        return True

    def derive(self, wm) -> dict:
        return {"all_outputs_found": True}


def build_elaborator() -> Elaborator:
    """
    [설계 자유] 어떤 ElaborationRule을 등록할지.
               ActiveSoarAgent.solve() 호출 시 생성.
    """
    rules = [
        InputTaskToStateRule("elaborate_input_task"),
        NeedsTargetSelectionRule("needs_target_selection"),
        HasPendingComparisonRule("has_pending_comparison"),
        AllComparisonsDoneRule("all_comparisons_done"),
        ReadyForPatternExtractionRule("ready_for_pattern_extraction"),
        ReadyForGeneralizationRule("ready_for_generalization"),
        ReadyForPredictionRule("ready_for_prediction"),
        AllOutputsFoundRule("all_outputs_found"),
    ]
    return Elaborator(rules)
