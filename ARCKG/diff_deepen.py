"""
DIFF 깊이 분석: 비교 결과에서 (1) 크다/작다 ordering, (2) 집합 포함관계 추출.
막혔을 때만 호출하는 추가 분석용. 모든 comparison receipt에 기본 추가하지 않음.

- ordering: color는 숫자로 표기되지만 lt/gt 적용 안 함. coordinate, pos 하위 row_index/col_index,
  area, size 및 그 성분(height, width 등)만 orderable.
- set_relation: 두 집합을 비교한 DIFF 리프에 대해 포함된다/포함되지 않는다/공통 있음/없음.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


# path(소문자)에 이 중 하나라도 있으면 크기 비교(lt/gt) 적용. color는 제외.
ORDERABLE_PATH_PARTS = frozenset(
    ("area", "size", "height", "width", "row_index", "col_index", "coordinate", "pos")
)
# path에 이 중 하나라도 있으면 lt/gt 적용 안 함 (color는 숫자여도 순서 없음).
NON_ORDERABLE_PATH_PARTS = frozenset(("color",))


def _path_is_orderable(path: str) -> bool:
    """path가 orderable 속성인지. color 계열은 False, area/size/coordinate/pos/row_index/col_index 등은 True."""
    if not path:
        return False
    lower = path.lower()
    if any(p in lower for p in NON_ORDERABLE_PATH_PARTS):
        return False
    return any(p in lower for p in ORDERABLE_PATH_PARTS)


def _is_orderable_scalar(v: Any) -> bool:
    """int, float만 ordering 적용 (color는 숫자지만 path로 걸러짐)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _ordering(v1: Any, v2: Any) -> str | None:
    """v1, v2가 둘 다 숫자일 때 'lt' (v1 < v2) 또는 'gt' (v1 > v2). 같으면 None."""
    if not _is_orderable_scalar(v1) or not _is_orderable_scalar(v2):
        return None
    try:
        a, b = float(v1), float(v2)
        if a < b:
            return "lt"
        if a > b:
            return "gt"
    except (TypeError, ValueError):
        pass
    return None


def _to_hashable(e: Any) -> Any:
    """set에 넣기 위해 list -> tuple, 중첩 list 재귀."""
    if isinstance(e, list):
        return tuple(_to_hashable(x) for x in e)
    if isinstance(e, dict):
        return tuple(sorted((k, _to_hashable(v)) for k, v in e.items()))
    return e


def _set_relation(comp1: Any, comp2: Any) -> Dict[str, Any] | None:
    """
    두 집합(리스트/튜플)에 대해: 포함된다/포함되지 않는다/공통 있음/없음.
    반환: {"set_relation": "contained"|"contains"|"overlap"|"disjoint", "comp1_len", "comp2_len", "intersection_len"} 등.
    """
    try:
        it1 = list(comp1) if comp1 is not None else []
        it2 = list(comp2) if comp2 is not None else []
    except Exception:
        return None
    try:
        s1 = set(_to_hashable(e) for e in it1)
        s2 = set(_to_hashable(e) for e in it2)
    except TypeError:
        return None  # unhashable
    inter = s1 & s2
    if s1 == s2:
        return None  # COMM이면 DIFF가 아님; 여기선 DIFF만 오므로 무시하거나 "different"만 줄 수 있음
    if s1 <= s2:
        return {"set_relation": "contained", "comp1_len": len(s1), "comp2_len": len(s2), "intersection_len": len(inter)}
    if s1 >= s2:
        return {"set_relation": "contains", "comp1_len": len(s1), "comp2_len": len(s2), "intersection_len": len(inter)}
    if inter:
        return {"set_relation": "overlap", "comp1_len": len(s1), "comp2_len": len(s2), "intersection_len": len(inter)}
    return {"set_relation": "disjoint", "comp1_len": len(s1), "comp2_len": len(s2), "intersection_len": 0}


def _is_set_comparable(v: Any) -> bool:
    """리스트/튜플 등 집합으로 다룰 수 있는지."""
    return isinstance(v, (list, tuple)) and not _is_2d_grid(v)


def _is_2d_grid(v: Any) -> bool:
    """2D 그리드(리스트의 리스트)면 집합 비교에서 제외 (셀 단위 비교만 의미 있음)."""
    if not isinstance(v, (list, tuple)) or len(v) == 0:
        return False
    return isinstance(v[0], (list, tuple))


def _walk_category_add_ordering_and_set(
    node: Any,
    path_prefix: str,
    out_ordering: Dict[str, Dict[str, Any]],
    out_set: Dict[str, Dict[str, Any]],
) -> None:
    """
    get_comparison_data() 결과의 category 트리를 재귀 순회.
    - DIFF + 숫자 + path가 orderable(area/size/coordinate/pos/row_index/col_index 등, color 제외) → ordering 추가.
    - DIFF + comp1, comp2가 집합(1차원 리스트/튜플) → set_relation 추가.
    """
    if not isinstance(node, dict):
        return
    node_type = node.get("type")
    comp1 = node.get("comp1")
    comp2 = node.get("comp2")
    category = node.get("category")

    if category and isinstance(category, dict) and len(category) > 0:
        for key, sub in sorted(category.items(), key=lambda x: str(x[0])):
            sub_path = f"{path_prefix}.{key}" if path_prefix else key
            _walk_category_add_ordering_and_set(sub, sub_path, out_ordering, out_set)
        # 자식만 보면 됨; 현재 노드의 comp1/comp2는 보통 비어 있거나 요약
        return

    if node_type != "DIFF" or comp1 is None or comp2 is None or not path_prefix:
        return

    # (1) 숫자 + orderable path → lt/gt
    if _path_is_orderable(path_prefix):
        ord_val = _ordering(comp1, comp2)
        if ord_val is not None:
            out_ordering[path_prefix] = {
                "comp1": comp1,
                "comp2": comp2,
                "ordering": ord_val,
            }

    # (2) 집합 비교 가능한 리스트/튜플 → set_relation
    if _is_set_comparable(comp1) and _is_set_comparable(comp2):
        rel = _set_relation(comp1, comp2)
        if rel is not None:
            out_set[path_prefix] = {
                "comp1_len": rel.get("comp1_len"),
                "comp2_len": rel.get("comp2_len"),
                "intersection_len": rel.get("intersection_len"),
                "set_relation": rel["set_relation"],
            }


def deepen_diff_ordering(comparison_result: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    비교 결과에서 (1) orderable한 DIFF 숫자 리프에 대한 ordering(lt/gt),
    (2) 집합 DIFF에 대한 set_relation(contained/contains/overlap/disjoint) 추출.
    기존 receipt는 수정하지 않음.

    반환: 단일 dict에 두 종류 모두 넣음.
    - ordering 항목: "path": {"comp1", "comp2", "ordering": "lt"|"gt"}
    - set 항목: "path": {"set_relation", "comp1_len", "comp2_len", "intersection_len"}
    """
    result = comparison_result.get("result") if "result" in comparison_result else comparison_result
    if not isinstance(result, dict):
        return {}
    category = result.get("category")
    if not isinstance(category, dict):
        return {}
    out_ordering: Dict[str, Dict[str, Any]] = {}
    out_set: Dict[str, Dict[str, Any]] = {}
    for key, sub in category.items():
        _walk_category_add_ordering_and_set(sub, key, out_ordering, out_set)
    # path 충돌 방지: ordering은 그대로, set은 키에 _set 붙이거나 한 dict로 합침 (같은 path 나올 수 있음)
    out: Dict[str, Dict[str, Any]] = dict(out_ordering)
    for k, v in out_set.items():
        out[f"{k}_set"] = v
    return out
