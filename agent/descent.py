"""
Descent (모듈 A = intra) — 막혀야 내려간다 (P1: 계층 깊이는 *필요* 에 의해).

TASK→PAIR→GRID→OBJECT. 각 레벨에서 Inter 비교(모듈 C)를 시도하고, 목적 달성이
불가능하면(막힘) 다음 레벨로 intra-descend. 강제 하강 ✗ — 결정적 비교를 찾는 순간 멈춤.

각 레벨에서 *읽은 ARCKG 정보·비교 결과·schema* 를 WM substate(`examined`)에 기록한다
→ WM 로그로 "무슨 정보가 있고 무엇을 비교했나"가 보인다.
"""

from procedural_memory.DSL.util import pairs_of, role_of, is_foreground
from procedural_memory.DSL.property import (
    size, color, contents, grid_count, color_of, coordinate_of,
)
from procedural_memory.DSL.relation import select, compare_set, verdict
from program.anti_unification import anti_unify_objects, is_solvable, resolve_property
from agent.goal_stack import GoalStack, next_level

_GOAL = {
    "TASK": "solve task — Pa 의 출력 만들기",
    "PAIR": "Pa 에 빠진 grid(출력) 만들기",
    "GRID": "출력 grid 의 {size, color, contents} 정하기",
    "OBJECT": "출력 객체의 {위치, 색} 정하기 — 위치=COMM, 색=G0 에서",
}

_is_output = lambda g: role_of(g) == "output"
_sn = lambda node: ".".join(node.node_id.split(".")[1:])          # 짧은 라벨
_cols = lambda d: sorted(k for k, v in d.items() if v)            # color dict → 색 목록
_fgcolor = lambda d: next((k for k, v in d.items() if v and k != 0), None)


def _try_resolve(level: str, task) -> dict:
    """현재 레벨에서 결정적 비교를 시도. 반환: {decisive, reason, examined, evidence}."""
    if level == "TASK":
        examined = [f"TASK: example {len(task.example_pairs)}쌍, test {len(task.test_pairs)}쌍 (형제 TASK 없음)"]
        return {"decisive": False, "reason": "형제 TASK 없음 → 비교 0",
                "examined": examined, "evidence": None}

    if level == "PAIR":
        pairs = select(task, "pair")
        receipts = compare_set(pairs)
        examined = ["grid-count: " + ", ".join(f"{_sn(p)}={grid_count(p)}" for p in pairs)]
        examined += [f"compare({_sn(x)},{_sn(y)}) = {verdict(r)[0]}" for x, y, r in receipts]
        return {"decisive": False, "reason": "pair 비교는 grid-count 뿐 → 출력 grid 내용 미정",
                "examined": examined, "evidence": None}

    if level == "GRID":
        g1s = [g for p in pairs_of(task) for g in select(p, "grid", _is_output)]
        receipts = compare_set(g1s)
        examined = [f"{_sn(g)}: size={size(g)['height']}x{size(g)['width']}, colors={_cols(color(g))}"
                    for g in g1s]
        examined += [f"compare({_sn(x)},{_sn(y)}) = {verdict(r)[0]}, COMM={verdict(r)[2]}"
                     for x, y, r in receipts]
        all_comm = bool(receipts) and all(verdict(r)[0] == "COMM" for _, _, r in receipts)
        if all_comm:
            ref = g1s[0]
            evidence = {"size": size(ref), "color": color(ref), "contents": contents(ref)}
            return {"decisive": True, "reason": "모든 example G1 COMM → 공통 grid 가 답",
                    "examined": examined, "evidence": evidence}
        comm = verdict(receipts[0][2])[2] if receipts else []
        return {"decisive": False,
                "reason": f"부분 COMM (같음={comm}) — 출력이 입력에 의존 → OBJECT 로",
                "examined": examined, "evidence": None}

    if level == "OBJECT":
        fg = lambda g: select(g, "object", is_foreground)[0]
        examined = []
        examples = []
        for p in task.example_pairs:
            o0, o1 = fg(p.input_grid), fg(p.output_grid)
            examples.append((o0.to_json(), o1.to_json()))
            examined.append(
                f"{_sn(p)}: G0 obj(색 {_fgcolor(color_of(o0))} @{coordinate_of(o0)[0]}) "
                f"→ G1 obj(색 {_fgcolor(color_of(o1))} @{coordinate_of(o1)[0]})")
        schema = anti_unify_objects(examples, ["color", "coordinate"])
        out_sizes = [p.output_grid.to_json()["size"] for p in task.example_pairs]
        schema["grid_size"] = ({"kind": "const", "value": out_sizes[0]}
                               if all(s == out_sizes[0] for s in out_sizes)
                               else {"kind": "unexplained"})
        examined.append("anti-unify schema: " + ", ".join(f"{k}={v['kind']}" for k, v in schema.items()))
        decisive = is_solvable(schema)
        evidence = None
        if decisive:
            test_props = fg(task.test_pairs[0].input_grid).to_json()
            color_dict = resolve_property(schema["color"], test_props)
            evidence = {
                "schema": schema,
                "size": resolve_property(schema["grid_size"], test_props),
                "cells": resolve_property(schema["coordinate"], test_props),
                "color": _fgcolor(color_dict),
            }
        return {"decisive": decisive,
                "reason": "schema 전부 설명됨" if decisive else "schema 에 unexplained 있음",
                "examined": examined, "evidence": evidence}

    return {"decisive": False, "reason": f"미지원 level {level}",
            "examined": [], "evidence": None}


def descend_to_decisive(wm, task, on_level=None):
    """막힘 기반 descent 루프. 결정적 비교에 도달하면 (result, goal_stack) 반환.
    각 레벨에서 examined(읽은 ARCKG 정보·비교)를 WM substate 에 기록 → WM 로그 가시화."""
    gs = GoalStack(wm, _GOAL["TASK"])
    while True:
        level = gs.current_level()
        result = _try_resolve(level, task)
        wm.active["examined"] = result["examined"]      # WM 에 기록 → 로그로 보임
        if on_level:
            on_level(level, gs.current_goal(), result)
        if result["decisive"]:
            return result, gs
        nxt = next_level(level)
        if nxt is None:
            return result, gs
        gs.descend(nxt, _GOAL[nxt], result["reason"])
