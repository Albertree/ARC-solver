"""
Descent (모듈 A) + GoalStack(B) — 막혀야 내려간다 (P1). 그리고 *목표는 관측-주도*로
바뀐다: 레벨 진입 시 고정이 아니라, 새 observation(특히 비교 결과)을 받을 때마다 진화.

흐름(관측 → 가능?No → 비교 → 발견 → 목표 변경 → DSL?No → 하강)을 phase 단위로 기록한다.
각 비교는 *전체 receipt* 를 phase 에 담는다 (해설서가 per-property COMM/DIFF·점수를 표기).
"""

from procedural_memory.DSL.util import pairs_of, role_of, is_foreground
from procedural_memory.DSL.property import size, color, contents, grid_count
from procedural_memory.DSL.selection import select
from procedural_memory.DSL.relation import compare, verdict
from program.anti_unification import anti_unify_objects, is_solvable, resolve_property
from agent.goal_stack import GoalStack, next_level

_is_output = lambda g: role_of(g) == "output"
_sn = lambda n: ".".join(n.node_id.split(".")[1:])
_cols = lambda d: sorted(k for k, v in d.items() if v)
_fgcolor = lambda d: next((k for k, v in d.items() if v and k != 0), None)

ROOT_GOAL = "이 문제(Task)를 해결한다 = Pa 의 출력 만들기"


def _ph(desc, goal, compares=None, tag="observe"):
    return {"desc": desc, "goal": goal, "compares": compares or [], "tag": tag}


def _try_resolve(level, task, goal):
    """현재 레벨 처리 → {decisive, reason, phases, evidence, goal}. 목표는 관측 중 진화."""
    P = []

    if level == "TASK":
        P.append(_ph(f"TASK 받음 — Task.property 확인: example {len(task.example_pairs)}쌍, "
                     f"test {len(task.test_pairs)}쌍", goal))
        P.append(_ph("목표 달성에 지금 할 수 있는 비교? — 형제 TASK 없음 → 비교 0", goal, tag="decide"))
        return {"decisive": False, "reason": "형제 TASK 없음 → 비교 0 → 하강",
                "phases": P, "evidence": None, "goal": goal}

    if level == "PAIR":
        pairs = select(task, "pair")
        for p in pairs:
            P.append(_ph(f"PAIR {_sn(p)} 관측 — grid_count = {grid_count(p)}", goal))
        P.append(_ph("목표 달성 가능? — No. 가진 PAIR.property 끼리 비교", goal, tag="decide"))
        recs = compare(pairs, pairs)
        P.append(_ph("PAIR 끼리 비교 (Inter-Pair, property=grid_count)", goal,
                     compares=[(_sn(x), _sn(y), r) for x, y, r in recs], tag="compare"))
        goal = "Pa 의 빠진 grid(출력) 만들기 — grid_count 를 P0·P1 과 같게"
        P.append(_ph("Pa 의 grid_count 가 다름 발견 → <b>목표 변경</b>", goal, tag="goal"))
        P.append(_ph("이 변화를 만들 DSL 있나? — grid 추가 DSL 없음 → 더 깊이", goal, tag="decide"))
        return {"decisive": False, "reason": "grid_count 차이는 알았으나 만들 DSL 없음 → 하강",
                "phases": P, "evidence": None, "goal": goal}

    if level == "GRID":
        ex = task.example_pairs
        goal = "Pa 의 GRID 3요소(size·color·contents) 찾기"
        P.append(_ph(f"{_sn(ex[0].input_grid)} 관측 — GRID 구성요소 3개(size·color·contents) 인지 "
                     f"→ <b>목표 변경</b>", goal, tag="goal"))
        # 한 pair 안 grid 비교 (Intra-Pair: 변화 전 G0 ↔ 변화 후 G1) — 흐름상 거침
        intra = []
        for p in ex:
            r = compare([p.input_grid], [p.output_grid])
            intra.append((_sn(p.input_grid), _sn(p.output_grid), r[0][2]))
        P.append(_ph("한 Pair 안 G0(변화전)↔G1(변화후) 비교 — 어느 쪽이 답인지 모르니 흐름상 거침", goal,
                     compares=intra, tag="compare"))
        goal = "Pa.G1(변화 후)의 3요소 찾기"
        P.append(_ph("test 에 없는 건 G1(출력) → 비교 대상 = 변화 후 G1 확정 → <b>목표 구체화</b>", goal, tag="goal"))
        # G1 끼리 비교 (Inter-Pair-Grid)
        g1s = [g for p in pairs_of(task) for g in select(p, "grid", _is_output)]
        recs = compare(g1s, g1s)
        P.append(_ph("규칙: '모든 Pair 의 변화가 같아야'. G1=변화후. example G1 끼리 비교", goal,
                     compares=[(_sn(x), _sn(y), r) for x, y, r in recs], tag="compare"))
        all_comm = bool(recs) and all(verdict(r)[0] == "COMM" for _, _, r in recs)
        if all_comm:
            ref = g1s[0]
            P.append(_ph("size·color·contents 가 G1 전부 COMM → 3요소 모두 결정 (출력 고정)", goal, tag="decide"))
            return {"decisive": True, "reason": "모든 example G1 COMM → 공통 grid 가 답",
                    "phases": P, "evidence": {"size": size(ref), "color": color(ref), "contents": contents(ref)},
                    "goal": goal}
        commk = verdict(recs[0][2])[2] if recs else []
        goal = "Pa.G1 의 contents 유추 (size·color 는 G1 공통으로 결정됨)"
        P.append(_ph(f"size·color 는 G1 공통(={commk}) → 결정. 하지만 contents 다름 → "
                     f"변화 후끼리론 부족 → <b>목표 변경</b>", goal, tag="goal"))
        P.append(_ph("contents 는 G0·G1 다 달라 'after'끼리론 불가 → 변화(G0→G1) 관계에 초점 → OBJECT 하강",
                     goal, tag="decide"))
        return {"decisive": False, "reason": f"size·color 는 COMM, contents 다름 → 변화 관계로 OBJECT 하강",
                "phases": P, "evidence": None, "goal": goal}

    if level == "OBJECT":
        goal = "G0→G1 변화를 해소하는 DSL 조합 찾기 (Pa.G1.contents)"
        P.append(_ph("변화(G0→G1) 관계에 초점 — 각 Pair 의 G0·G1 객체 관측", goal, tag="goal"))
        fg = lambda g: select(g, "object", is_foreground)[0]

        def ctx(grid):
            o = fg(grid).to_json()
            gs = grid.to_json()["size"]
            return {"color": o["color"], "coordinate": o["coordinate"],
                    "grid_size": gs, "grid_h": gs["height"], "grid_w": gs["width"]}

        examples, change_cmp = [], []
        for p in task.example_pairs:
            o0, o1 = fg(p.input_grid), fg(p.output_grid)
            examples.append((ctx(p.input_grid), ctx(p.output_grid)))
            change_cmp.append((f"{_sn(p)}.G0.obj", f"{_sn(p)}.G1.obj", compare([o0], [o1])[0][2]))
        P.append(_ph("G0.objects ↔ G1.objects 집단 비교 → 점수 높은 매칭을 '가장 유력한 변화쌍'으로 "
                     "[지금은 전경 객체 1개로 단순화 — 항목 ③ 논의 대상]", goal,
                     compares=change_cmp, tag="compare"))

        schema = anti_unify_objects(examples, ["color", "coordinate", "grid_size"])
        P.append(_ph("그 변화쌍의 property 별 변화를 우선순위 탐색으로 일반화 (anti-unify): "
                     + ", ".join(f"{k}={v.get('via', v['kind'])}" for k, v in schema.items()), goal, tag="decide"))
        decisive = is_solvable(schema)
        evidence = None
        if decisive:
            test = ctx(task.test_pairs[0].input_grid)
            evidence = {"schema": schema,
                        "size": resolve_property(schema["grid_size"], test),
                        "cells": resolve_property(schema["coordinate"], test),
                        "color": _fgcolor(resolve_property(schema["color"], test))}
        return {"decisive": decisive,
                "reason": "변화 schema 전부 설명됨" if decisive else "schema 에 unexplained 있음",
                "phases": P, "evidence": evidence, "goal": goal}

    return {"decisive": False, "reason": f"미지원 level {level}", "phases": P, "evidence": None, "goal": goal}


def descend_to_decisive(wm, task, on_level=None):
    """막힘 기반 descent. 목표는 관측-주도로 진화하며 thread 된다."""
    gs = GoalStack(wm, ROOT_GOAL)
    goal = ROOT_GOAL
    while True:
        level = gs.current_level()
        result = _try_resolve(level, task, goal)
        goal = result["goal"]                                  # 진화한 목표를 이어감
        wm.active["goal"] = goal
        wm.active["examined"] = [p["desc"] for p in result["phases"]]
        if on_level:
            on_level(level, goal, result)
        if result["decisive"]:
            return result, gs
        nxt = next_level(level)
        if nxt is None:
            return result, gs
        gs.descend(nxt, goal, result["reason"])
