"""
Working Memory: SOAR-style WME (identifier, attribute, value) triplets.
Single source of state for the decision cycle. Only written at init and in apply_effect.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, List, Optional, Tuple

# SOAR: State = Goal. S1 = top-level state identifier. S2 = first subgoal state.
STATE_ID = "S1"
SUBGOAL_STATE_ID = "S2"


def _wme_key(id_: str, attr: str, value: Any) -> Tuple[str, str, Any]:
    """Normalize value for WME identity (e.g. tuple for deficit)."""
    if isinstance(value, list):
        value = tuple(value)
    return (id_, attr, value)


class WorkingMemory:
    """
    WM as a set of WMEs (Working Memory Elements) = (identifier, attribute, value).
    Root = S1 (state = goal). SOAR: ^type, ^operator, ^impasse 반영.
    """
    # SOAR 예약 attribute와 사용자 attribute 구분 (found 등에서 제외할 이름)
    _RESERVED_ATTRS = frozenset((
        "goal", "task-id", "focus", "deficit", "tried", "subgoal",
        "type", "operator", "impasse", "superstate",
    ))

    __slots__ = ("_wmes", "_task", "_state_stack")

    def __init__(
        self,
        *,
        goal: Any = None,
        task: Any = None,
        focus: Any = "TASK",
        deficits: Optional[list] = None,
        found: Optional[dict] = None,
        tried: Optional[list] = None,
        subgoal: Any = None,
    ):
        self._wmes: List[Tuple[str, str, Any]] = []
        self._task: Any = task
        # ^superstate chain: [S1] or [S1, S2]. Decision cycle runs on bottom (current) state.
        self._state_stack: List[str] = [STATE_ID]

        self.add_wme(STATE_ID, "type", "state")
        self.add_wme(STATE_ID, "task-id", (task or {}).get("task_id") or "")
        if goal is not None:
            self.add_wme(STATE_ID, "goal", goal)
        self.add_wme(STATE_ID, "focus", focus)
        if subgoal is not None:
            self.add_wme(STATE_ID, "subgoal", subgoal)

        for d in (deficits or []):
            self.add_wme(STATE_ID, "deficit", d if isinstance(d, tuple) else tuple(d) if isinstance(d, list) else d)
        for op in (tried or []):
            self.add_wme(STATE_ID, "tried", op)
        for k, v in (found or {}).items():
            self.add_wme(STATE_ID, k, v)

    def add_wme(self, id_: str, attr: str, value: Any) -> None:
        """Add one WME (triplet). Same (id, attr, value) is not duplicated."""
        key = _wme_key(id_, attr, value)
        for i, w in enumerate(self._wmes):
            if _wme_key(w[0], w[1], w[2]) == key:
                return
        self._wmes.append((id_, attr, value))

    def remove_wme(self, id_: str, attr: str, value: Any) -> bool:
        """Remove one WME matching (id, attr, value). Returns True if removed."""
        key = _wme_key(id_, attr, value)
        for i, w in enumerate(self._wmes):
            if _wme_key(w[0], w[1], w[2]) == key:
                self._wmes.pop(i)
                return True
        return False

    def remove_wmes_by_attr(self, id_: str, attr: str) -> int:
        """Remove all WMEs with (id, attr). Returns count removed."""
        removed = 0
        i = len(self._wmes) - 1
        while i >= 0:
            if self._wmes[i][0] == id_ and self._wmes[i][1] == attr:
                self._wmes.pop(i)
                removed += 1
            i -= 1
        return removed

    def get_values(self, id_: str, attr: str) -> List[Any]:
        """Return list of values for (id, attr)."""
        return [w[2] for w in self._wmes if w[0] == id_ and w[1] == attr]

    def get_value(self, id_: str, attr: str) -> Optional[Any]:
        """Return first value for (id, attr) or None."""
        for w in self._wmes:
            if w[0] == id_ and w[1] == attr:
                return w[2]
        return None

    def get_all_wmes(self) -> List[Tuple[str, str, Any]]:
        """Return snapshot of all WMEs (for display / matching)."""
        return list(self._wmes)

    def current_state_id(self) -> str:
        """Bottom of ^superstate chain; decision cycle runs here (SOAR)."""
        return self._state_stack[-1]

    # --- Compatibility API (same as before for rules/operators) ---

    @property
    def goal(self) -> Any:
        return self.get_value(STATE_ID, "goal")

    @property
    def task(self) -> Any:
        return self._task

    @task.setter
    def task(self, value: Any) -> None:
        self._task = value
        tid = (value or {}).get("task_id") or ""
        self.remove_wmes_by_attr(STATE_ID, "task-id")
        self.add_wme(STATE_ID, "task-id", tid)

    @property
    def focus(self) -> Any:
        return self.get_value(STATE_ID, "focus")

    @property
    def deficits(self) -> list:
        return list(self.get_values(STATE_ID, "deficit"))

    @property
    def found(self) -> dict:
        out = {}
        for w in self._wmes:
            if w[0] != STATE_ID:
                continue
            attr = w[1]
            if attr in self._RESERVED_ATTRS:
                continue
            out[attr] = w[2]
        return out

    @property
    def operator(self) -> Optional[Any]:
        """현재 선택/적용된 연산자 (SOAR: current state ^operator)."""
        return self.get_value(self.current_state_id(), "operator")

    @property
    def impasse(self) -> Optional[Any]:
        """현재 impasse 유형 (no-change, tie 등). 없으면 None. Bottom state 기준."""
        return self.get_value(self.current_state_id(), "impasse")

    def set_operator(self, name: str) -> None:
        """Apply 후 선택된 연산자 기록. 다음 결정 전에 clear. Current state에 기록."""
        sid = self.current_state_id()
        self.remove_wmes_by_attr(sid, "operator")
        self.add_wme(sid, "operator", name)

    def clear_operator(self) -> None:
        """Current state의 ^operator 제거."""
        self.remove_wmes_by_attr(self.current_state_id(), "operator")

    def set_impasse(self, impasse_type: str) -> None:
        """Impasse 발생 시 (no-change, tie 등). Current state에 기록."""
        sid = self.current_state_id()
        self.remove_wmes_by_attr(sid, "impasse")
        self.add_wme(sid, "impasse", impasse_type)

    def clear_impasse(self) -> None:
        """Current state의 ^impasse 제거."""
        self.remove_wmes_by_attr(self.current_state_id(), "impasse")

    @property
    def tried(self) -> list:
        return list(self.get_values(STATE_ID, "tried"))

    @property
    def subgoal(self) -> Any:
        """하위 목표 값. S1에만 보관; S2 존재 여부는 state_stack 길이로 판단."""
        return self.get_value(STATE_ID, "subgoal")

    def apply_effect(self, effect: dict[str, Any]) -> None:
        """
        Apply an effect dict (from operator). Updates WM only via add/remove WMEs.
        """
        if not effect:
            return
        if "add_tried" in effect:
            v = effect["add_tried"]
            for name in ([v] if isinstance(v, str) else v):
                self.add_wme(STATE_ID, "tried", name)
        if "remove_tried" in effect:
            v = effect["remove_tried"]
            for name in ([v] if isinstance(v, str) else v):
                self.remove_wme(STATE_ID, "tried", name)
        if "remove_deficits" in effect:
            to_remove = effect["remove_deficits"]
            if not isinstance(to_remove, list):
                to_remove = [to_remove]
            for d in to_remove:
                t = d if isinstance(d, tuple) else tuple(d) if isinstance(d, list) else d
                self.remove_wme(STATE_ID, "deficit", t)
        if "add_found" in effect:
            for k, v in effect["add_found"].items():
                self.remove_wmes_by_attr(STATE_ID, k)
                self.add_wme(STATE_ID, k, v)
        if "set_focus" in effect:
            self.remove_wmes_by_attr(STATE_ID, "focus")
            self.add_wme(STATE_ID, "focus", effect["set_focus"])
        if "set_subgoal" in effect:
            self.remove_wmes_by_attr(STATE_ID, "subgoal")
            self.add_wme(STATE_ID, "subgoal", effect["set_subgoal"])
        if effect.get("clear_subgoal"):
            self.remove_wmes_by_attr(STATE_ID, "subgoal")
        if "add_deficits" in effect:
            for d in effect["add_deficits"]:
                self.add_wme(STATE_ID, "deficit", d if isinstance(d, tuple) else tuple(d) if isinstance(d, list) else d)

    def set_subgoal(self, value: Any) -> None:
        """Impasse 시 S2 push: (S2 ^superstate S1), (S2 ^type state), (S2 ^impasse no-change). S1 ^subgoal 값 유지."""
        self.remove_wmes_by_attr(STATE_ID, "subgoal")
        if value is not None:
            self.add_wme(STATE_ID, "subgoal", value)
        if SUBGOAL_STATE_ID not in self._state_stack:
            self.add_wme(SUBGOAL_STATE_ID, "superstate", STATE_ID)
            self.add_wme(SUBGOAL_STATE_ID, "type", "state")
            self.add_wme(SUBGOAL_STATE_ID, "impasse", "no-change")
            self._state_stack.append(SUBGOAL_STATE_ID)

    def clear_subgoal(self) -> None:
        """S2 WME 전부 제거 후 state stack을 [S1]으로. S1 ^subgoal·^impasse 제거."""
        while len(self._state_stack) > 1:
            sid = self._state_stack.pop()
            i = len(self._wmes) - 1
            while i >= 0:
                if self._wmes[i][0] == sid:
                    self._wmes.pop(i)
                i -= 1
        self.remove_wmes_by_attr(STATE_ID, "subgoal")
        self.remove_wmes_by_attr(STATE_ID, "impasse")

    def to_matchable(self) -> dict[str, Any]:
        """Snapshot for rule matching."""
        return {
            "goal": self.goal,
            "focus": self.focus,
            "deficits": list(self.deficits),
            "tried": list(self.tried),
            "subgoal": self.subgoal,
            "found_keys": list(self.found.keys()),
        }

    def copy(self) -> WorkingMemory:
        c = WorkingMemory.__new__(WorkingMemory)
        c._wmes = [ (w[0], w[1], deepcopy(w[2])) for w in self._wmes ]
        c._task = self._task
        c._state_stack = list(self._state_stack)
        return c

    def __repr__(self) -> str:
        return (
            f"WorkingMemory(goal={self.goal!r}, focus={self.focus!r}, "
            f"deficits={len(self.deficits)}, tried={len(self.tried)}, subgoal={self.subgoal!r})"
        )
