"""
Active exploration operators: deficit-driven, component-in/between analysis, 0/1/2-order relations.
SOAR 연산자: 결핍·포커스에 따라 분석(내부/간), 0·1·2차 관계 생성.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from soar.wm import WorkingMemory


def _task_from_wm(wm: WorkingMemory):
    """Load full TASK (ARCKG) from wm.task dict. Returns None if missing task_id."""
    task = wm.task or {}
    task_id = task.get("task_id") or ""
    if not task_id:
        return None
    try:
        from managers.arc_manager import ARCManager
        return ARCManager.from_hex_code(task_id)
    except Exception:
        return None


def _grid_by_label(task: Any, label: str):
    """P0G0, P0G1, P1G0, PaG0 등 그리드 라벨 → GRID 컴포넌트."""
    if not task or not label or len(label) < 3:
        return None
    try:
        p_part = label[1]
        g_part = label[2] if len(label) > 2 else "0"
        grid_idx = int(g_part) if g_part.isdigit() else 0
        if p_part.isdigit():
            pair_idx = int(p_part)
            if pair_idx < len(task.example_pairs):
                pair = task.example_pairs[pair_idx]
                return pair.input_grid if grid_idx == 0 else pair.output_grid
        else:
            test_idx = ord(p_part.lower()) - ord("a")
            if 0 <= test_idx < len(task.test_pairs):
                return task.test_pairs[test_idx].input_grid
    except Exception:
        pass
    return None


def _component_by_label(task: Any, label: str):
    """
    Resolve short label to component.
    P0G0 = pair0 input grid, P0G1 = pair0 output grid; PaG0 = test pair 0 input.
    P0G0O0, P0G0O1 = object 0, 1 of that grid (같은 그리드 내 객체).
    """
    if not task or not label:
        return None
    # Object-level: P0G0O0, P0G0O1, ...
    if "O" in label.upper() and len(label) >= 6:
        try:
            i = label.upper().index("O")
            grid_label = label[:i]
            obj_part = label[i + 1:]
            obj_idx = int(obj_part) if obj_part.isdigit() else -1
            grid = _grid_by_label(task, grid_label)
            if grid is not None and getattr(grid, "objects", None) and 0 <= obj_idx < len(grid.objects):
                return grid.objects[obj_idx]
        except Exception:
            pass
        return None
    return _grid_by_label(task, label)


def _grid_labels_for_task(task: Any) -> List[Tuple[str, Any]]:
    """(label, grid) for all grids: P0G0, P0G1, P1G0, P1G1, PaG0, ..."""
    out: List[Tuple[str, Any]] = []
    if not task:
        return out
    for i, pair in enumerate(getattr(task, "example_pairs", [])):
        out.append((f"P{i}G0", pair.input_grid))
        out.append((f"P{i}G1", pair.output_grid))
    for i in range(len(getattr(task, "test_pairs", []))):
        letter = chr(ord("a") + i)
        test_pair = task.test_pairs[i]
        out.append((f"P{letter}G0", test_pair.input_grid))
    return out


def _ensure_property(comp: Any) -> None:
    if comp is None:
        return
    if not getattr(comp, "property", None) or not comp.property:
        if hasattr(comp, "update_property"):
            comp.update_property()
        comp.property = getattr(comp, "property", {})


# ---------- Deficit helpers ----------

def _has_deficit(wm: WorkingMemory, level: str, attr: str, context: Any) -> bool:
    for d in wm.deficits:
        if not isinstance(d, (list, tuple)) or len(d) < 3:
            continue
        if d[0] == level and d[1] == attr and d[2] == context:
            return True
    return False


def _has_relation_deficit(wm: WorkingMemory, order: int, key: Tuple) -> bool:
    return _has_deficit(wm, "RELATION", order, key)


def _relation_found_key(order: int, key: Any) -> str:
    if order == 0:
        return f"relation_0_{key[0]}" if isinstance(key, (list, tuple)) else f"relation_0_{key}"
    if order == 1 and isinstance(key, (list, tuple)) and len(key) >= 2:
        return f"relation_1_{key[0]}-{key[1]}"
    if order == 2 and isinstance(key, (list, tuple)) and len(key) >= 2:
        return f"relation_2_{key[0]}_{key[1]}".replace("(", "").replace(")", "").replace(" ", "")
    return f"relation_{order}_{key}"


# ---------- analyze-inside: 한 컴포넌트 내부 분석 (0차 property, 필요 시 자식 간 1차) ----------

def cond_analyze_inside(wm: WorkingMemory) -> bool:
    """Propose when focus is on a concrete scope (PAIR, GRID or OBJECT) and we have deficits or no 0th yet."""
    if not wm.deficits:
        return False
    focus = wm.focus
    if focus == "TASK":
        return False
    if not isinstance(focus, (list, tuple)) or len(focus) < 2:
        return False
    # (PAIR, i, GRID) or (PAIR, i, OBJECT) or (INTER_PAIR, GRID)
    if "analyze-inside" in wm.tried:
        return False  # avoid immediate retry; other ops can clear tried
    return True


def effect_analyze_inside(wm: WorkingMemory) -> dict[str, Any]:
    """Ensure 0th property for current focus component; optionally 1st between children (e.g. input vs output of same pair)."""
    task = _task_from_wm(wm)
    if task is None:
        return {"add_tried": ["analyze-inside"]}
    focus = wm.focus
    add_found: Dict[str, Any] = {}
    remove_deficits: List[Tuple] = []

    # Focus (PAIR, i, GRID) -> component P{i}G0, P{i}G1; ensure property and optionally compare P{i}G0 vs P{i}G1
    if isinstance(focus, (list, tuple)) and len(focus) >= 3 and focus[0] == "PAIR":
        pair_idx = focus[1]
        level = focus[2]
        if pair_idx < len(task.example_pairs) and level in ("GRID", "OBJECT", "PIXEL"):
            pair = task.example_pairs[pair_idx]
            if level == "GRID":
                for g_idx, grid in enumerate([pair.input_grid, pair.output_grid]):
                    label = f"P{pair_idx}G{g_idx}"
                    _ensure_property(grid)
                    key_0 = ("P{}G{}".format(pair_idx, g_idx),)
                    add_found[_relation_found_key(0, key_0)] = getattr(grid, "property", {})
                    if _has_relation_deficit(wm, 0, key_0):
                        remove_deficits.append(("RELATION", 0, key_0))
                # 1st within pair: P{i}G0 vs P{i}G1
                try:
                    from ARCKG.comparison import compare
                    res = compare(pair.input_grid, pair.output_grid, save=False)
                    key_1 = (f"P{pair_idx}G0", f"P{pair_idx}G1")
                    add_found[_relation_found_key(1, key_1)] = res
                    if _has_relation_deficit(wm, 1, key_1):
                        remove_deficits.append(("RELATION", 1, key_1))
                except Exception:
                    pass

    return {
        "add_tried": ["analyze-inside"],
        "add_found": add_found,
        **({"remove_deficits": remove_deficits} if remove_deficits else {}),
    }


# ---------- analyze-between: 두 컴포넌트 간 비교 (1차 관계) ----------

def cond_analyze_between(wm: WorkingMemory) -> bool:
    """Propose when we have at least one RELATION 1 deficit not yet in found."""
    if not wm.deficits:
        return False
    for d in wm.deficits:
        if isinstance(d, (list, tuple)) and len(d) >= 3 and d[0] == "RELATION" and d[1] == 1:
            key = d[2]
            if isinstance(key, (list, tuple)) and len(key) >= 2 and wm.found.get(_relation_found_key(1, tuple(key))) is None:
                return True
    return False


def effect_analyze_between(wm: WorkingMemory) -> dict[str, Any]:
    """Resolve one RELATION 1 deficit: compare two nodes by label, store in found."""
    task = _task_from_wm(wm)
    if task is None:
        return {"add_tried": ["analyze-between"]}
    for d in wm.deficits:
        if not isinstance(d, (list, tuple)) or len(d) < 3 or d[0] != "RELATION" or d[1] != 1:
            continue
        key = d[2]
        if not isinstance(key, (list, tuple)) or len(key) < 2:
            continue
        label1, label2 = key[0], key[1]
        c1 = _component_by_label(task, label1)
        c2 = _component_by_label(task, label2)
        if c1 is None or c2 is None:
            continue
        try:
            from ARCKG.comparison import compare
            res = compare(c1, c2, save=False)
            rk = _relation_found_key(1, (label1, label2))
            return {
                "add_tried": ["analyze-between"],
                "add_found": {rk: res},
                "remove_deficits": [("RELATION", 1, key)],
            }
        except Exception:
            continue
    return {"add_tried": ["analyze-between"]}


# ---------- create-relation-0: 0차 property 확보 ----------

def cond_create_relation_0(wm: WorkingMemory) -> bool:
    return any(
        isinstance(d, (list, tuple)) and len(d) >= 3 and d[0] == "RELATION" and d[1] == 0
        for d in wm.deficits
    ) and "create-relation-0" not in wm.tried


def effect_create_relation_0(wm: WorkingMemory) -> dict[str, Any]:
    task = _task_from_wm(wm)
    if task is None:
        return {"add_tried": ["create-relation-0"]}
    for d in wm.deficits:
        if not isinstance(d, (list, tuple)) or len(d) < 3 or d[0] != "RELATION" or d[1] != 0:
            continue
        key = d[2]
        label = key[0] if isinstance(key, (list, tuple)) else key
        comp = _component_by_label(task, str(label))
        if comp is None:
            continue
        _ensure_property(comp)
        rk = _relation_found_key(0, key)
        return {
            "add_tried": ["create-relation-0"],
            "add_found": {rk: getattr(comp, "property", {})},
            "remove_deficits": [("RELATION", 0, key)],
        }
    return {"add_tried": ["create-relation-0"]}


# ---------- create-relation-1: 1차 관계 생성 ----------

def cond_create_relation_1(wm: WorkingMemory) -> bool:
    return any(
        isinstance(d, (list, tuple)) and len(d) >= 3 and d[0] == "RELATION" and d[1] == 1
        for d in wm.deficits
    ) and "create-relation-1" not in wm.tried


def effect_create_relation_1(wm: WorkingMemory) -> dict[str, Any]:
    return effect_analyze_between(wm)


# ---------- create-relation-2: 2차 관계 생성 (두 1차 결과 비교) ----------

def cond_create_relation_2(wm: WorkingMemory) -> bool:
    return any(
        isinstance(d, (list, tuple)) and len(d) >= 3 and d[0] == "RELATION" and d[1] == 2
        for d in wm.deficits
    ) and "create-relation-2" not in wm.tried


def effect_create_relation_2(wm: WorkingMemory) -> dict[str, Any]:
    t = wm.task
    task_hex = (t.get("task_id") if isinstance(t, dict) else getattr(t, "hex_code", None) or getattr(t, "task_id", None)) if t else ""
    for d in wm.deficits:
        if not isinstance(d, (list, tuple)) or len(d) < 3 or d[0] != "RELATION" or d[1] != 2:
            continue
        key = d[2]
        if not isinstance(key, (list, tuple)) or len(key) < 2:
            continue
        # key = (("P0G0","P0G1"), ("P1G0","P1G1")) for 2nd order between two 1st-order edges
        k1, k2 = key[0], key[1]
        r1 = wm.found.get(_relation_found_key(1, k1)) if isinstance(k1, (list, tuple)) else wm.found.get(_relation_found_key(1, (k1, k2)))
        r2 = wm.found.get(_relation_found_key(1, k2)) if isinstance(k2, (list, tuple)) and k1 != k2 else None
        if isinstance(k1, (list, tuple)) and isinstance(k2, (list, tuple)):
            r1 = wm.found.get(_relation_found_key(1, tuple(k1)))
            r2 = wm.found.get(_relation_found_key(1, tuple(k2)))
        if r1 is None or r2 is None:
            continue
        res1 = r1.get("result") if isinstance(r1, dict) else r1
        res2 = r2.get("result") if isinstance(r2, dict) else r2
        if res1 is None or res2 is None:
            continue
        edge_id1 = r1.get("edge_id") if isinstance(r1, dict) else None
        edge_id2 = r2.get("edge_id") if isinstance(r2, dict) else None
        if not edge_id1:
            edge_id1 = f"E_{k1[0]}-{k1[1]}" if isinstance(k1, (list, tuple)) and len(k1) >= 2 else "E_unknown1"
        if not edge_id2:
            edge_id2 = f"E_{k2[0]}-{k2[1]}" if isinstance(k2, (list, tuple)) and len(k2) >= 2 else "E_unknown2"
        try:
            from ARCKG.comparison import compare
            res = compare(res1, res2, save=False, edge_id1=edge_id1, edge_id2=edge_id2, task_hex=task_hex)
            rk = _relation_found_key(2, key)
            return {
                "add_tried": ["create-relation-2"],
                "add_found": {rk: res},
                "remove_deficits": [("RELATION", 2, key)],
            }
        except Exception:
            continue
    return {"add_tried": ["create-relation-2"]}


# ---------- add-relation-deficits: 탐색 목표 추가 (능동적으로 부족한 관계를 결핍으로 등록) ----------

def cond_add_relation_deficits(wm: WorkingMemory) -> bool:
    """Propose when we have output deficits but no relation deficits yet — add 1st-order deficits for each example pair."""
    if not wm.deficits:
        return False
    has_output_deficit = any(
        isinstance(d, (list, tuple)) and len(d) >= 2 and d[1] == "contents"
        for d in wm.deficits
    )
    has_relation_deficit = any(
        isinstance(d, (list, tuple)) and len(d) >= 2 and d[0] == "RELATION"
        for d in wm.deficits
    )
    return has_output_deficit and not has_relation_deficit and "add-relation-deficits" not in wm.tried


def effect_add_relation_deficits(wm: WorkingMemory) -> dict[str, Any]:
    """Add RELATION 1 deficits for each example pair (P{i}G0 vs P{i}G1) to drive analysis."""
    task = _task_from_wm(wm)
    if task is None:
        return {"add_tried": ["add-relation-deficits"]}
    new_deficits: List[Tuple] = []
    try:
        n = len(task.example_pairs)
    except Exception:
        n = 0
    for i in range(n):
        key = (f"P{i}G0", f"P{i}G1")
        new_deficits.append(("RELATION", 1, key))
    if not new_deficits:
        return {"add_tried": ["add-relation-deficits"]}
    return {
        "add_tried": ["add-relation-deficits"],
        "add_deficits": new_deficits,
    }


# ---------- extract-grid-property-conclusions: G0 vs G1 비교에서 size/color/contents 결론만 WM에 저장 ----------
# 프로그램이 아니라 정보만: "size가 같다 → size는 있는 걸 사용한다" 같은 결론을 found에 저장.

def _grid_property_conclusions_from_comparison(comp_result: dict) -> Dict[str, str]:
    """
    From a grid-vs-grid comparison result, return minimal conclusions for WM.
    comp_result: full compare(G0, G1) output with 'result' containing category.size/color/contents.
    Returns e.g. {"size": "unchanged", "color": "changed", "contents": "changed"}.
    """
    out: Dict[str, str] = {}
    res = comp_result.get("result") if isinstance(comp_result, dict) else comp_result
    if not isinstance(res, dict):
        return out
    cat = res.get("category") or {}
    for prop in ("size", "color", "contents"):
        c = cat.get(prop)
        if isinstance(c, dict) and "type" in c:
            out[prop] = "unchanged" if c.get("type") == "COMM" else "changed"
        else:
            out[prop] = "changed"
    return out


def cond_extract_grid_property_conclusions(wm: WorkingMemory) -> bool:
    """Propose when we have output deficit and not yet extracted grid property conclusions (정보만 WM에)."""
    if "extract-grid-property-conclusions" in wm.tried:
        return False
    if not wm.deficits:
        return False
    has_output = any(
        isinstance(d, (list, tuple)) and len(d) >= 2 and d[1] == "contents"
        for d in wm.deficits
    )
    return has_output


def effect_extract_grid_property_conclusions(wm: WorkingMemory) -> dict[str, Any]:
    """
    For each example pair, compare input_grid vs output_grid (G0 vs G1), extract size/color/contents
    conclusions and store in WM as information only (no program).
    Keys: grid_inv_P{i}_size, grid_inv_P{i}_color, grid_inv_P{i}_contents = "unchanged" | "changed".
    If relation_1_PiG0-PiG1 already in found, use it; else run compare and also store it.
    """
    task = _task_from_wm(wm)
    if task is None:
        return {"add_tried": ["extract-grid-property-conclusions"]}
    add_found: Dict[str, Any] = {}
    found = wm.found
    pairs = getattr(task, "example_pairs", [])
    try:
        from ARCKG.comparison import compare
    except Exception:
        return {"add_tried": ["extract-grid-property-conclusions"]}
    for i, pair in enumerate(pairs):
        rk = _relation_found_key(1, (f"P{i}G0", f"P{i}G1"))
        comp = found.get(rk)
        if comp is None:
            _ensure_property(pair.input_grid)
            _ensure_property(pair.output_grid)
            comp = compare(pair.input_grid, pair.output_grid, save=False)
            add_found[rk] = comp
        if not isinstance(comp, dict):
            continue
        conclusions = _grid_property_conclusions_from_comparison(comp)
        pair_char = str(i)
        for prop, value in conclusions.items():
            add_found[f"grid_inv_P{pair_char}_{prop}"] = value
    if not add_found:
        return {"add_tried": ["extract-grid-property-conclusions"]}
    return {
        "add_tried": ["extract-grid-property-conclusions"],
        "add_found": add_found,
    }


# ---------- compare-objects-within-grid: 같은 그리드 내 객체 쌍 비교 (같은 색끼리) ----------

def cond_compare_objects_within_grid(wm: WorkingMemory) -> bool:
    """Propose when we have output deficit and haven't run within-grid object comparisons yet."""
    if not wm.deficits:
        return False
    has_output = any(
        isinstance(d, (list, tuple)) and len(d) >= 2 and d[1] == "contents"
        for d in wm.deficits
    )
    if not has_output:
        return False
    if "compare-objects-within-grid" in wm.tried:
        return False
    return True


def effect_compare_objects_within_grid(wm: WorkingMemory) -> dict[str, Any]:
    """For each grid (P0G0, P0G1, P1G0, P1G1, PaG0), compare same-color object pairs; store relation_1_*."""
    task = _task_from_wm(wm)
    if task is None:
        return {"add_tried": ["compare-objects-within-grid"]}
    try:
        from ARCKG.comparison import compare
    except Exception:
        return {"add_tried": ["compare-objects-within-grid"]}
    add_found: Dict[str, Any] = {}
    for label, grid in _grid_labels_for_task(task):
        objs = getattr(grid, "objects", None)
        if not objs or len(objs) < 2:
            continue
        # Group by color (같은 색 object끼리만 비교). color가 dict면 해시 가능한 키로.
        by_color = {}
        for idx, obj in enumerate(objs):
            _ensure_property(obj)
            color = getattr(obj, "color", None)
            if color is None:
                prop = getattr(obj, "property", None) or {}
                color = prop.get("color")
            key = _color_key_for_grouping(color)
            by_color.setdefault(key, []).append(idx)
        for color, indices in by_color.items():
            if len(indices) < 2:
                continue
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    oi, oj = indices[i], indices[j]
                    try:
                        # save=True, no label1/label2 → compare() uses LCA of component IDs;
                        # same-grid objects have LCA = grid → file under N_P{p}/N_G{g}/E_O{o1}-O{o2}.json
                        res = compare(objs[oi], objs[oj], save=True)
                        key = f"relation_1_{label}O{oi}-{label}O{oj}"
                        add_found[key] = res
                    except Exception:
                        continue
    if not add_found:
        return {"add_tried": ["compare-objects-within-grid"]}
    return {
        "add_tried": ["compare-objects-within-grid"],
        "add_found": add_found,
    }


# ---------- predict-from-invariant: found의 _diff_ordering으로 COMM/DIFF 매칭 후 예측 ----------

def _object_area_gt_count_from_found(found: Dict[str, Any], grid_label: str, n_objects: int) -> Dict[int, int]:
    """
    For each object index, count how many same-grid pairs have this object's area > other (area ordering).
    ordering 'gt' => comp1 > comp2 (first object wins); 'lt' => comp1 < comp2 (second object wins).
    """
    counts: Dict[int, int] = {i: 0 for i in range(n_objects)}
    for k, v in found.items():
        if not k.endswith("_diff_ordering") or not isinstance(v, dict) or grid_label not in k:
            continue
        base = k.replace("_diff_ordering", "")
        if not base.startswith("relation_1_"):
            continue
        parts = base[10:].split("-")
        if len(parts) != 2:
            continue
        a, b = parts[0], parts[1]
        if not a.startswith(grid_label) or not b.startswith(grid_label):
            continue
        try:
            oa = int(a.split("O")[-1])
            ob = int(b.split("O")[-1])
        except Exception:
            continue
        if oa == ob or not (0 <= oa < n_objects and 0 <= ob < n_objects):
            continue
        for path, info in v.items():
            if "_set" in path or not isinstance(info, dict):
                continue
            if "area" not in path.lower():
                continue
            ord_val = info.get("ordering")
            if ord_val == "gt":
                counts[oa] = counts.get(oa, 0) + 1
            elif ord_val == "lt":
                counts[ob] = counts.get(ob, 0) + 1
    return counts


def _color_key_for_grouping(c: Any) -> Any:
    """Hashable key for color grouping (dict/list → tuple)."""
    if c is None:
        return "unknown"
    if isinstance(c, dict):
        return tuple(sorted((k, v) for k, v in c.items()))
    if isinstance(c, (list, tuple)):
        return tuple(c)
    return c


def _max_area_object_per_color(task: Any, grid_label: str, area_gt_count: Dict[int, int]) -> Dict[Any, int]:
    """For grid, group objects by color; in each group, return object index that has area_gt_count == len(group)-1."""
    grid = _grid_by_label(task, grid_label)
    if grid is None or not getattr(grid, "objects", None):
        return {}
    objs = grid.objects
    by_color: Dict[Any, List[int]] = {}
    for idx in range(len(objs)):
        obj = objs[idx]
        _ensure_property(obj)
        prop = getattr(obj, "property", None) or {}
        color = prop.get("color") or getattr(obj, "color", "unknown")
        key = _color_key_for_grouping(color)
        by_color.setdefault(key, []).append(idx)
    out: Dict[Any, int] = {}
    for color, indices in by_color.items():
        n = len(indices)
        for i in indices:
            if area_gt_count.get(i, 0) == n - 1:
                out[color] = i
                break
    return out


def cond_predict_from_invariant(wm: WorkingMemory) -> bool:
    """Propose when we have output deficit and object-level _diff_ordering for at least one example grid AND one test grid (PaG0)."""
    if not wm.deficits:
        return False
    has_output_deficit = any(
        isinstance(d, (list, tuple)) and len(d) >= 2 and d[1] == "contents"
        for d in wm.deficits
    )
    if not has_output_deficit:
        return False
    object_deepen = [k for k in wm.found if k.endswith("_diff_ordering") and "O" in k]
    if not object_deepen:
        return False
    n_test = max(1, len((wm.task or {}).get("test", [])))
    has_ex = any("P0G0O" in k or "P1G0O" in k for k in object_deepen)
    has_test = any(f"P{chr(ord('a')+i)}G0O" in k for k in object_deepen for i in range(n_test))
    if not has_ex or not has_test:
        return False
    if "predict-from-invariant" in wm.tried:
        return False
    return True


def effect_predict_from_invariant(wm: WorkingMemory) -> dict[str, Any]:
    """
    Use found relation_1_*_diff_ordering: same-color object with area_gt count == (n_same_color-1) is 'max area'.
    Predict test output: copy test input, color the max-area same-color object's region blue (COMM/DIFF 매칭).
    """
    task = _task_from_wm(wm)
    if task is None:
        return {"add_tried": ["predict-from-invariant"]}
    n_test = max(1, len(getattr(task, "test_pairs", [])))
    add_found: Dict[str, Any] = {}
    remove_deficits: List[Tuple] = []
    import copy as copy_mod

    for test_idx in range(n_test):
        letter = chr(ord("a") + test_idx)
        pa_g0_label = f"P{letter}G0"
        test_grid = _grid_by_label(task, pa_g0_label)
        if test_grid is None:
            continue
        test_objs = getattr(test_grid, "objects", None)
        if not test_objs:
            continue
        area_gt_test = _object_area_gt_count_from_found(wm.found, pa_g0_label, len(test_objs))
        max_test = _max_area_object_per_color(task, pa_g0_label, area_gt_test)
        if not max_test:
            continue
        in_view = getattr(test_grid, "view", None) or getattr(test_grid, "colorgrid", None)
        if in_view is None:
            continue
        out_view = copy_mod.deepcopy(in_view)
        h, w = len(out_view), len(out_view[0]) if out_view else 0
        blue_color = 4
        for _color, obj_idx_test in max_test.items():
            obj_test = test_objs[obj_idx_test]
            pos_t = getattr(obj_test, "pos", None) or (getattr(obj_test, "property", None) or {}).get("pos", {})
            if isinstance(pos_t, dict):
                rt = pos_t.get("row_index", 0)
                ct = pos_t.get("col_index", 0)
            else:
                rt, ct = (pos_t[0], pos_t[1]) if len(pos_t) >= 2 else (0, 0)
            cg = getattr(obj_test, "colorgrid", None) or getattr(obj_test, "view", None)
            if not cg:
                continue
            for di, row in enumerate(cg):
                for dj, val in enumerate(row):
                    if di + rt < h and dj + ct < w:
                        out_view[di + rt][dj + ct] = blue_color
            add_found[f"output_test_{test_idx}"] = out_view
            remove_deficits.append(("GRID", "contents", f"output-test-{test_idx}"))
            break

    return {
        "add_tried": ["predict-from-invariant"],
        "add_found": add_found,
        **({"remove_deficits": remove_deficits} if remove_deficits else {}),
    }


# ---------- deepen-diff-ordering: 막혔을 때 DIFF 리프에서 크다/작다(ordering) 추출 ----------

def cond_deepen_diff_ordering(wm: WorkingMemory) -> bool:
    """Propose when we have deficits and at least one relation in found not yet deepened."""
    if not wm.deficits:
        return False
    for k in wm.found:
        if (k.startswith("relation_1_") or k.startswith("relation_2_")) and not k.endswith("_diff_ordering"):
            if f"deepen-diff-ordering:{k}" not in wm.tried:
                return True
    return False


_MAX_DEEPEN_PER_CYCLE = 15


def effect_deepen_diff_ordering(wm: WorkingMemory) -> dict[str, Any]:
    """Deepen up to _MAX_DEEPEN_PER_CYCLE relations. Prefer object-level (O), then test grid (PaG0)."""
    try:
        from ARCKG.diff_deepen import deepen_diff_ordering
    except Exception:
        return {"add_tried": ["deepen-diff-ordering:no-module"]}
    candidates = []
    for k in wm.found:
        if (k.startswith("relation_1_") or k.startswith("relation_2_")) and not k.endswith("_diff_ordering"):
            if f"deepen-diff-ordering:{k}" in wm.tried:
                continue
            if not isinstance(wm.found.get(k), dict):
                continue
            has_o = "O" in k
            is_test = "PaG0" in k or "PbG0" in k
            candidates.append((not has_o, not is_test, k))
    if not candidates:
        return {}
    candidates.sort(key=lambda x: (x[0], x[1], x[2]))
    add_found: Dict[str, Any] = {}
    add_tried: List[str] = []
    for i, (_, _, k) in enumerate(candidates):
        if i >= _MAX_DEEPEN_PER_CYCLE:
            break
        val = wm.found.get(k)
        ordering_map = deepen_diff_ordering(val)
        add_found[f"{k}_diff_ordering"] = ordering_map
        add_tried.append(f"deepen-diff-ordering:{k}")
    if not add_found:
        return {}
    return {"add_tried": add_tried, "add_found": add_found}


# ---------- Registry: extend OPERATORS for active agent ----------

from soar.operators import OperatorSpec

ACTIVE_OPERATORS: Dict[str, OperatorSpec] = {
    "analyze-inside": OperatorSpec(cond_analyze_inside, effect_analyze_inside),
    "analyze-between": OperatorSpec(cond_analyze_between, effect_analyze_between),
    "create-relation-0": OperatorSpec(cond_create_relation_0, effect_create_relation_0),
    "create-relation-1": OperatorSpec(cond_create_relation_1, effect_create_relation_1),
    "create-relation-2": OperatorSpec(cond_create_relation_2, effect_create_relation_2),
    "add-relation-deficits": OperatorSpec(cond_add_relation_deficits, effect_add_relation_deficits),
    "extract-grid-property-conclusions": OperatorSpec(cond_extract_grid_property_conclusions, effect_extract_grid_property_conclusions),
    "compare-objects-within-grid": OperatorSpec(cond_compare_objects_within_grid, effect_compare_objects_within_grid),
    "deepen-diff-ordering": OperatorSpec(cond_deepen_diff_ordering, effect_deepen_diff_ordering),
    "predict-from-invariant": OperatorSpec(cond_predict_from_invariant, effect_predict_from_invariant),
}


def get_active_operators() -> Dict[str, OperatorSpec]:
    return dict(ACTIVE_OPERATORS)


def merged_operators() -> Dict[str, OperatorSpec]:
    """OPERATORS + ACTIVE_OPERATORS. Active agent uses this."""
    from soar.operators import OPERATORS
    out = dict(OPERATORS)
    out.update(ACTIVE_OPERATORS)
    return out
