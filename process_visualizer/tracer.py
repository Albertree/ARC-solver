"""
process_visualizer/tracer.py — ARBOR 풀이 과정을 *타임스텝* 단위로 잡아 시각화용 구조 데이터로.

타임스텝 = ARBOR 에 *어떤 변화든 하나* 생긴 순간 (operator apply · impasse · 하강 · 복기 · 해결).
각 타임스텝마다 담는 것:
  · WM 전체 + 직전 대비 diff(+추가 / -삭제 / ~변경)
  · 발화한 규칙(operator): 이름 · 소스 경로 · 설명 · 무엇이 trigger(하이라잇 키) · 스코프 종류
  · 목표 스택(계층) — 상위목표 아래 어떤 하위목표가 섰는지
  · 탐색/비교 스코프 — 비교 대상·결과, DSL 탐색 구역, 조합(수형도), anti-unify 시도
(파일명이 stdlib `trace` 와 겹치지 않도록 tracer.py)
"""

import os
import sys
import copy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import program.search as search
from managers.arc_manager import ARCManager
from agent.wm import WorkingMemory
from agent.wm_logger import _wm_as_entries
from agent.io import inject_arc_task
from agent.goal import Goal, deposit_goal
from agent.decision import run, GENERAL_OPS


# 규칙(operator)별 메타: 어느 경로의 규칙인지 · 무엇을 하나 · 무엇이 trigger(WM 키) · 스코프 종류
OP_META = {
    # 일반 operator (→ wiki arbor-operators). scope 는 ④ 패널 분기 키.
    "observe":    {"path": "agent/decision.py → DSL/property (frame)",
                   "doc": "노드 property 구조 관측 → 목표 구체화",
                   "trig": ["need", "goal", "object-selection"], "scope": "frame"},
    "select":     {"path": "agent/decision.py → DSL/selection",
                   "doc": "비교·조립 대상(범위·항목) 선택",
                   "trig": ["goal"], "scope": "select"},
    "compare":    {"path": "agent/decision.py → DSL/relation",
                   "doc": "두 scope 비교 → 속성별 COMM/DIFF (원시·고정·범위 = scope)",
                   "trig": ["goal", "compared", "frame"], "scope": "compare"},
    "search":     {"path": "agent/decision.py → procedural_memory/dsl_search",
                   "doc": "need 의 effect 를 내는 DSL 탐색",
                   "trig": ["need", "goal"], "scope": "search"},
    "generalize": {"path": "agent/decision.py → program/anti_unification",
                   "doc": "pair별 구체값 → 추상 schema (anti-unify)",
                   "trig": ["frame", "object-selection"], "scope": "search-tree"},
    "compose":    {"path": "agent/decision.py → DSL/transformation",
                   "doc": "transformation DSL 조합 → 결과 조립",
                   "trig": ["grid-props", "dsl-search", "change-schema"], "scope": "compose"},
    # pseudo-operator (구조 변화)
    "start":   {"path": "agent/io.py → inject_arc_task()",
                "doc": "환경의 task 를 WM 입력 링크에 주입하고 루트 목표를 올린다",
                "trig": ["input-link", "goal"], "scope": "none"},
    "impasse": {"path": "agent/wm.push_substate", "doc": "제안 operator 없음 → no-change impasse",
                "trig": ["goal"], "scope": "none"},
    "descend": {"path": "agent/decision.run", "doc": "substate push — 한 계층 깊이 (holds→effect 변신)",
                "trig": ["level"], "scope": "none"},
    "unwind":  {"path": "agent/decision.run", "doc": "하위목표 해소 → substate pop, 상위 need 충족 전파",
                "trig": ["goal"], "scope": "none"},
    "solved":  {"path": "agent/decision.run", "doc": "answer 기록 — 해결",
                "trig": [], "scope": "none"},
}


def _match_table(level, proposed_names):
    """이 레벨에서 스캔되는 operator 들 + 조건 통과(propose) 여부 — match 타일용.
    ✓=propose 조건 통과(후보) · ✗=탈락. (조건 단위 drill 은 추후 — 지금은 op·doc·pass/fail.)"""
    rows = []
    for g in GENERAL_OPS:
        if not any(lvl == level for (_, _, lvl) in g["variants"]):
            continue
        nm = g["name"]
        rows.append({"name": nm, "doc": OP_META.get(nm, {}).get("doc", ""),
                     "passed": nm in proposed_names})
    return rows


def _entries(wm):
    out = []
    for e in _wm_as_entries(wm):
        out.append({"id": e.identifier, "attr": e.attribute, "val": e.value,
                    "path": e.path_key, "depth": e.depth, "root": e.is_root})
    return out


def _diff(curr, prev):
    """직전 대비 +추가/~변경/=동일, 그리고 사라진 것 -삭제 를 표시."""
    pmap = {e["path"]: e["val"] for e in prev}
    cpaths = set()
    res = []
    for e in curr:
        cpaths.add(e["path"])
        st = ("added" if e["path"] not in pmap
              else "changed" if pmap[e["path"]] != e["val"] else "same")
        res.append(dict(e, status=st))
    for e in prev:
        if e["path"] not in cpaths:
            res.append(dict(e, status="removed"))
    return res


def _goals(wm):
    """목표 스택(계층): S1→Sx 각 substate 의 goal 을 깊이 indent 와 함께."""
    states = [("S1", wm.s1)] + [(f"S{i+2}", s) for i, s in enumerate(wm._substate_stack)]
    out = []
    for depth, (sid, s) in enumerate(states):
        g = s.get("goal")
        if not g:
            continue
        n = g.get("need")
        ns = None
        if n:
            ns = f"{n['attr']}: {n['have']}→{n['want']}  requires={n['requires']}"
            if n.get("holds"):
                ns += f"  holds={n['holds']}"
        out.append({"sid": sid, "level": s.get("level"), "intent": g.get("intent"),
                    "status": g.get("status"), "need": ns, "depth": depth,
                    "active": depth == len(states) - 1})
    return out


def _built(wm):
    for s in [wm.s1] + wm._substate_stack:
        if s.get("built-grid"):
            return s["built-grid"]
    return None


def _schema_summary(sc):
    if not sc:
        return None
    return {k: {"kind": v.get("kind"), "via": v.get("via"),
                "offset": v.get("offset"), "base": v.get("base"),
                "value": v.get("value"), "attr": v.get("attr")} for k, v in sc.items()}


def build_trace(repo, task_id):
    mgr = ARCManager(data_root=os.path.join(ROOT, "data"))
    rel = f"{repo}/{task_id}.json"
    task = mgr.load_task(rel)
    gt = mgr.test_ground_truth(rel)

    # step = WM 상태(한 번의 WM 변화로 도달). substep = 그 상태에서 *시작하는* 사이클:
    #   view(①상태 머리) → propose(②후보+①trigger) → decide(②선택) → compute(④) → apply(①diff)
    # 각 step 의 마지막 substep(apply) 의 WM 변화가 다음 step 의 상태를 만든다.
    #   · 일반 사이클(apply): view→propose→decide→compute→apply
    #   · impasse 사이클: view→propose(∅)→decide(impasse)→apply(descend)   (compute 없음)
    #   · input(start) = 맨 앞(task 그림, 번호 없음).  unwind/solved = 맨 뒤 output(번호 없음).
    # step0 = WM 씨앗(init) 을 읽는 첫 사이클. 씨앗은 view 머리에서 초록(genesis)으로.
    steps = []
    prev = {"entries": [], "goals": []}
    big = {"n": 0}
    pend = {"data": None}        # impasse 의 (markers, level) 버퍼 (descend 사이클에서 propose/decide 로)
    search.TRACE = []

    def _mk(phase, wm_v, goals_v, opname, meta, kind, level, markers, show_trig,
            head=False, tail=False):
        steps.append({"i": len(steps), "big": big["n"], "phase": phase,
                      "op": opname, "meta": meta, "kind": kind, "level": level,
                      "wm": wm_v, "goals": goals_v, "show_trigger": show_trig,
                      "head": head, "tail": tail, **markers})

    def snap(step, kind, what, proposed, wm):
        opname = what if kind == "apply" else kind
        meta = OP_META.get(opname, OP_META.get(kind, {"path": "", "doc": kind, "trig": [], "scope": "none"}))
        level = wm.active.get("level")
        g = wm.active.get("goal") or {}
        markers = {
            "need": g.get("need"), "built": _built(wm), "proposed": list(proposed),
            "compared": copy.deepcopy(wm.active.get("compared")),
            "comparisons": copy.deepcopy(wm.active.get("comparisons")),
            "grid_props": copy.deepcopy(wm.active.get("grid-props")),
            "dsl_search": copy.deepcopy(wm.active.get("dsl-search")),
            "frame": copy.deepcopy(wm.active.get("frame")),
            "obj_sel": copy.deepcopy(wm.active.get("object-selection")),
            "schema": _schema_summary(wm.active.get("change-schema")),
        }
        after = _entries(wm)
        agoals = _goals(wm)
        before_entries = prev["entries"]
        before = [dict(e, status="same") for e in before_entries]     # 읽는 상태 (변화 없음 = 회색)
        diff = _diff(after, before_entries)                            # 이 사이클의 WM 변화 (+/-/~)
        bg = prev["goals"]                                             # 읽는 상태의 목표
        # view 머리 WM: step0(씨앗) 은 초록(genesis), 그 외엔 '읽는 상태'를 회색으로.
        view_wm = _diff(before_entries, []) if big["n"] == 0 else before

        def commit():
            prev["entries"] = after
            prev["goals"] = agoals
            big["n"] += 1

        if kind == "start":
            # 맨 앞 input = task 그림만 (번호 없음). 씨앗은 step0 view 머리에서 보여준다.
            _mk("input", [], bg, "—", meta, "input", level, markers, False)    # task 주입 (operator 아님)
            prev["entries"] = after; prev["goals"] = agoals    # 씨앗 커밋 → step0 의 '읽는 상태' = 씨앗
        elif kind == "apply":   # 자연 사이클: view → match → propose → preference → select → compute → apply
            markers["match"] = _match_table(level, markers["proposed"])   # 규칙 스캔표 (mechanism)
            _mk("view",       view_wm, bg,     opname, meta, kind, level, markers, False, head=True)
            _mk("match",      before,  bg,     opname, meta, kind, level, markers, True)   # trigger 는 match 부터
            _mk("propose",    before,  bg,     opname, meta, kind, level, markers, True)
            _mk("preference", before,  bg,     opname, meta, kind, level, markers, False)
            _mk("select",     before,  bg,     opname, meta, kind, level, markers, False)
            _mk("compute",    before,  bg,     opname, meta, kind, level, markers, False)
            _mk("apply",      diff,    agoals, opname, meta, kind, level, markers, False)
            commit()
        elif kind == "impasse":                    # apply(=descend) 는 descend 사이클이 — (markers,level) 버퍼
            pend["data"] = (dict(markers), level)
        elif kind == "descend":   # impasse 사이클: 관측→스캔→후보∅→impasse(판정·여기서 끝)→하강(해결)
            im_m, im_lv = pend["data"] if pend["data"] else (markers, level)
            # 도메인 op(전부 ✗) + descend(impasse 해결법, ✓) — descend 도 후보로 노출
            im_m["match"] = _match_table(im_lv, im_m.get("proposed", [])) + [
                {"name": "descend", "doc": "아래 계층 노드 확인 (impasse 해결법)", "passed": True}]
            NONE = {"path": "", "doc": "", "trig": [], "scope": "none"}     # 아직 operator 미정
            _mk("view",    view_wm, bg, "—",       NONE, "observe", im_lv, im_m, False, head=True)
            _mk("match",   before,  bg, "—",       NONE, "observe", im_lv, im_m, True)    # trigger 부터
            _mk("propose", before,  bg, "—",       NONE, "observe", im_lv, im_m, False)
            _mk("select",  before,  bg, "impasse", OP_META["impasse"], "impasse", im_lv, im_m, False)  # impasse 판정
            _mk("descend", diff, agoals, "descend", meta, "descend", level, markers, False)            # 해결: 하강
            pend["data"] = None
            commit()
        elif kind in ("unwind", "solved"):         # 맨 뒤 output (번호 없음 · tail)
            _mk(kind, diff if kind == "unwind" else [], agoals,
                opname, meta, kind, level, markers, False, tail=True)
            commit()

    # 씨앗은 ActiveSoarAgent.solve 와 *동일* 하게 — 보는 것(visualizer)=도는 것(실제 경로).
    # (solve: inject → level=TASK → 루트 목표 → rejected 슬롯 → decision.run)
    wm = WorkingMemory()
    inject_arc_task(task, wm)
    wm.s1["level"] = "TASK"
    deposit_goal(wm, Goal("이 task 를 푼다", scope="TASK"))
    wm.s1["rejected"] = []          # 틀린 답 누적 슬롯 (attempt 1 = 빈 리스트). solve 가 retry 시 채움.
    snap(-1, "start", "start", [], wm)

    res = run(wm, task, on_step=snap)
    attempts = list(search.TRACE)
    search.TRACE = None
    for s in steps:                               # anti-unify 탐색 시도 → generalize 의 compute(④)에 부착
        if s["op"] == "generalize" and s["phase"] in ("compute", "apply"):
            s["attempts"] = attempts

    answer = wm.s1.get("answer")
    grids = {
        "train": [{"in": p.input_grid.raw, "out": p.output_grid.raw} for p in task.example_pairs],
        "test": [{"in": p.input_grid.raw, "gt": gt[i]} for i, p in enumerate(task.test_pairs)],
    }
    return {"id": task_id, "repo": repo, "grids": grids, "answer": answer,
            "correct": bool(gt) and answer == gt[0], "result": res, "steps": steps}
