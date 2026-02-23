"""
Find a DSL expression (over ARCKG) that evaluates to the given values for each pair.
Used when abstracting anti-unification variables so v1 = coord_of(object_at_input(input_grid, 0))
instead of v1 = [(1, 1)].
"""

import ast
from typing import List, Any, Optional, Tuple

from program_gen import value_dsl


def _normalize_value(v: Any) -> Any:
    """Parse string to Python value if needed; normalize for comparison."""
    if v is None:
        return None
    if isinstance(v, str):
        try:
            return ast.literal_eval(v.strip())
        except (ValueError, SyntaxError):
            return v
    if isinstance(v, list):
        return [tuple(x) if isinstance(x, list) else x for x in v]
    if isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], (int, float)) and isinstance(v[1], (int, float)):
        return tuple(int(x) for x in v)
    return v


def _values_equal(a: Any, b: Any) -> bool:
    """Compare two values (list of coords, int color, etc.)."""
    na = _normalize_value(a)
    nb = _normalize_value(b)
    if na is None or nb is None:
        return na == nb
    # Normalize [(r,c)] <-> (r,c) for selection-style values
    if isinstance(na, list) and len(na) == 1 and isinstance(nb, (list, tuple)) and len(nb) == 2:
        na = na[0]
    elif isinstance(nb, list) and len(nb) == 1 and isinstance(na, (list, tuple)) and len(na) == 2:
        nb = nb[0]
    if type(na) != type(nb):
        if isinstance(na, (list, tuple)) and len(na) == 1:
            return _values_equal(na[0], nb)
        if isinstance(nb, (list, tuple)) and len(nb) == 1:
            return _values_equal(na, nb[0])
        return False
    if isinstance(na, (list, tuple)):
        if len(na) != len(nb):
            return False
        return all(_values_equal(x, y) for x, y in zip(na, nb))
    return na == nb


def _evaluate_candidate(
    candidate_name: str,
    task,
    pair_indices: List[int],
) -> List[Any]:
    """Evaluate a candidate expression for each pair. Returns list of values, one per pair."""
    results = []
    for idx in pair_indices:
        if idx >= len(task.example_pairs):
            results.append(None)
            continue
        pair = task.example_pairs[idx]
        input_grid = pair.input_grid
        if not hasattr(input_grid, "objects") or input_grid.objects is None:
            results.append(None)
            continue
        # Dispatch by candidate name and compute value
        if "selection_left_top_of(object_at_input(" in candidate_name:
            i = _parse_object_index(candidate_name, "selection_left_top_of(object_at_input(input_grid, ")
            obj = value_dsl.object_at_input(input_grid, i)
            results.append(value_dsl.selection_left_top_of(obj))
        elif "left_top_of(object_at_input(" in candidate_name:
            i = _parse_object_index(candidate_name, "left_top_of(object_at_input(input_grid, ")
            obj = value_dsl.object_at_input(input_grid, i)
            results.append(value_dsl.left_top_of(obj))
        elif "center_of(object_at_input(" in candidate_name:
            i = _parse_object_index(candidate_name, "center_of(object_at_input(input_grid, ")
            obj = value_dsl.object_at_input(input_grid, i)
            results.append(value_dsl.center_of(obj))
        elif "coords_of(object_at_input(" in candidate_name:
            i = _parse_object_index(candidate_name, "coords_of(object_at_input(input_grid, ")
            obj = value_dsl.object_at_input(input_grid, i)
            results.append(value_dsl.coords_of(obj))
        elif "color_of(object_at_input(" in candidate_name:
            i = _parse_object_index(candidate_name, "color_of(object_at_input(input_grid, ")
            obj = value_dsl.object_at_input(input_grid, i)
            results.append(value_dsl.color_of(obj))
        else:
            results.append(None)
    return results


def _parse_object_index(candidate_name: str, prefix: str) -> int:
    """Extract object index from candidate string like '...input_grid, 0))'."""
    if prefix not in candidate_name:
        return 0
    start = candidate_name.index(prefix) + len(prefix)
    rest = candidate_name[start:]
    num = []
    for c in rest:
        if c in "0123456789":
            num.append(c)
        else:
            break
    return int("".join(num)) if num else 0


def _build_candidates(max_objects: int = 10) -> List[str]:
    """Candidate expression strings (to be used in generated code)."""
    candidates = []
    for i in range(max_objects):
        candidates.append(f"selection_left_top_of(object_at_input(input_grid, {i}))")
        candidates.append(f"left_top_of(object_at_input(input_grid, {i}))")
        candidates.append(f"center_of(object_at_input(input_grid, {i}))")
        candidates.append(f"coords_of(object_at_input(input_grid, {i}))")
        candidates.append(f"color_of(object_at_input(input_grid, {i}))")
    return candidates


def find_expression_for_values(
    task_hex_code: str,
    values_by_pair: List[Any],
    pair_indices: Optional[List[int]] = None,
) -> Optional[str]:
    """
    Find a DSL expression that, when evaluated for each pair, gives the corresponding value.

    Args:
        task_hex_code: Task id (loads task via ARCManager).
        values_by_pair: [val0, val1, ...] concrete values for each pair (from anti-unify subst).
        pair_indices: [0, 1, ...] which pair index each value corresponds to. Default [0,1,...,n-1].

    Returns:
        Expression string to embed in generated code (e.g. "left_top_of(object_at_input(input_grid, 0))"),
        or None if no matching expression found.
    """
    if not values_by_pair:
        return None
    try:
        from managers.arc_manager import ARCManager
        task = ARCManager.from_hex_code(task_hex_code)
    except Exception:
        return None

    if pair_indices is None:
        pair_indices = list(range(len(values_by_pair)))

    if len(pair_indices) != len(values_by_pair):
        return None

    # Determine max object index to try from task
    max_objs = 0
    for idx in pair_indices:
        if idx < len(task.example_pairs):
            grid = task.example_pairs[idx].input_grid
            if hasattr(grid, "objects") and grid.objects is not None:
                max_objs = max(max_objs, len(grid.objects))
    max_objs = max(max_objs, 10)

    candidates = _build_candidates(max_objs)

    for cand in candidates:
        try:
            evaluated = _evaluate_candidate(cand, task, pair_indices)
            if len(evaluated) != len(values_by_pair):
                continue
            if all(_values_equal(evaluated[j], values_by_pair[j]) for j in range(len(values_by_pair))):
                return cand
        except Exception:
            continue
    return None


def expression_subst_from_arckg(
    task_hex_code: str,
    all_subst: List[dict],
    pair_indices: Optional[List[int]] = None,
) -> dict:
    """
    For each variable in the merged substitution, try to find an ARCKG-based expression.
    Returns dict mapping "?v1" -> "left_top_of(...)" or "?v1" -> first_concrete_value if not found.
    """
    if not all_subst:
        return {}
    merged = all_subst[0]
    for d in all_subst[1:]:
        merged = {**merged, **d}
    if pair_indices is None:
        n = len(all_subst)
        pair_indices = list(range(n))

    result = {}
    for var, values in merged.items():
        if not isinstance(values, tuple) or len(values) < 2:
            first = values[0] if isinstance(values, tuple) and values else values
            result[var] = first if isinstance(first, str) else repr(first)
            continue
        values_list = list(values)
        expr = find_expression_for_values(task_hex_code, values_list, pair_indices)
        if expr is not None:
            result[var] = expr
        else:
            first = values_list[0] if values_list[0] is not None else values_list[1]
            if _is_whole_term(first):
                result[var] = tuple(values_list)
            else:
                result[var] = first if isinstance(first, str) else repr(first)
    return result


def _is_whole_term(t: Any) -> bool:
    """True if t is a term tuple (apply_DSL, assign, return, raw), not an argument value."""
    if not isinstance(t, tuple) or len(t) < 1:
        return False
    return t[0] in ("apply_DSL", "assign", "return", "raw")
