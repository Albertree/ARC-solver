"""
explain_decisions — 결정 사이클(agent/decision.py)로 easy000a~i 를 풀며 *매 사이클*을
구조화 trace 로 잡아 아주 상세한 HTML 해설서(solutions_decision.html)로 낸다.

기존 solutions.html 과 스타일은 같되, 이번엔 *SOAR 결정 사이클*(propose→select→apply→
impasse→하강→복기)과 *단위 행동*(원시비교·심화비교·범위고정비교·DSL탐색·DSL조합)을
WM 상태변화와 함께 풀어 적는다.

실행: python tools/explain_decisions.py   → solutions_decision.html
"""

import os
import sys
import copy
import html

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from managers.arc_manager import ARCManager
from agent.wm import WorkingMemory
from agent.io import inject_arc_task
from agent.goal import Goal, deposit_goal
from agent.decision import run

TASKS = [f"easy000{c}" for c in "abcdefghi"]

PALETTE = {0: "#111", 1: "#0074D9", 2: "#FF4136", 3: "#2ECC40", 4: "#FFDC00",
           5: "#AAAAAA", 6: "#F012BE", 7: "#FF851B", 8: "#7FDBFF", 9: "#870C25"}


def grid_html(raw):
    if raw is None:
        return '<span class="muted">(숨김/예측대상)</span>'
    rows = "".join("<tr>" + "".join(
        f'<td style="background:{PALETTE.get(v, "#fff")}"></td>' for v in row) + "</tr>"
        for row in raw)
    return f'<table class="grid">{rows}</table>'


def _C(s):
    return f"<code>{html.escape(str(s))}</code>"


# ── 풀며 trace 수집 ─────────────────────────────────────────────────────
def solve_with_trace(task_id):
    mgr = ARCManager(data_root="data")
    task = mgr.load_task(task_id)
    gt = mgr.test_ground_truth(task_id)

    steps = []
    def on_step(step, kind, what, proposed, wm):
        steps.append({
            "step": step, "kind": kind, "what": what, "proposed": list(proposed),
            "level": wm.active.get("level"), "depth": wm.depth,
            "goal": copy.deepcopy(wm.active.get("goal")),
            "compared": copy.deepcopy(wm.active.get("compared")),
            "dsl_search": copy.deepcopy(wm.active.get("dsl-search")),
            "grid_props": copy.deepcopy(wm.active.get("grid-props")),
            "obj_sel": copy.deepcopy(wm.active.get("object-selection")),
            "schema": copy.deepcopy(wm.active.get("change-schema")),
            "frame": copy.deepcopy(wm.active.get("frame")),
        })

    wm = WorkingMemory()
    inject_arc_task(task, wm)
    wm.s1["level"] = "TASK"
    deposit_goal(wm, Goal("이 task 를 푼다", scope="TASK"))
    res = run(wm, task, on_step=on_step)
    answer = wm.s1.get("answer")

    # pair 별 roles (정적 사실)
    roles = []
    for p in list(task.example_pairs) + list(task.test_pairs):
        roles.append((p.node_id.split(".")[-1],
                      p.input_grid is not None, p.output_grid is not None,
                      p in task.test_pairs))
    grids = {
        "train": [(p.input_grid.raw, p.output_grid.raw) for p in task.example_pairs],
        "test": [(p.input_grid.raw, gt[i]) for i, p in enumerate(task.test_pairs)],
    }
    return {"id": task_id, "grids": grids, "roles": roles, "steps": steps,
            "res": res, "answer": answer, "correct": bool(gt) and answer == gt[0]}


# ── 바인딩(변화 schema) 설명 ────────────────────────────────────────────
def binding_desc(b):
    k = b.get("kind")
    if k == "from_g0":
        return f'<span class="ok">from_g0</span> — 출력 {b["attr"]} = 같은 pair 입력값 (보존)'
    if k == "const":
        return f'<span class="ok">const</span> — 모든 출력 동일: {_C(b["value"])}'
    if k == "coord":
        base = "입력 위치(in_coord)" if b["base"] == "in_coord" else "격자 크기(grid_dims)"
        extra = " = 모서리류" if b["base"] == "grid_dims" else ""
        return (f'<span class="ok">{html.escape(b["via"])}</span> — 출력좌표 = {base} + offset '
                f'{_C(b["offset"])}{extra}')
    return f'<span class="bad">{html.escape(str(k))}</span>'


# ── 한 사이클 step 을 서술 ──────────────────────────────────────────────
def _need_str(goal):
    n = (goal or {}).get("need")
    if not n:
        return "<span class='muted'>(없음)</span>"
    return (f"{_C(n['attr'])}: {_C(n['have'])}→{_C(n['want'])} "
            f"requires={_C(n['requires'])}" + (f" holds={_C(n['holds'])}" if n.get("holds") else ""))


def render_step(s):
    kind, op = s["kind"], s["what"]
    lvl = s["level"]
    proposed = "[" + ", ".join(s["proposed"]) + "]" if s["proposed"] else "∅"
    cls = {"impasse": "impasse", "solved": "decisive", "unwind": "decisive"}.get(kind, "")
    head = (f'<div class="step {cls}"><div class="lv">@{lvl}</div><div style="flex:1">'
            f'<div class="flow">cycle {s["step"]} · propose={_C(proposed)} · '
            f'<b>{html.escape(kind)}</b> {html.escape(op)}</div>')

    body = []
    g = s["goal"] or {}
    if kind == "apply" and op == "frame-grid":
        fr = s["frame"] or {}
        body.append("<b>관측 + 목표 구체화</b> — 만들 대상은 grid 이니, 대표 grid "
                    f"<code>{html.escape(fr.get('observed',''))}</code>(P0.G0)를 관측한다. "
                    "grid 의 property 구조(property DSL)는 "
                    f"<b>{len(fr.get('props',[]))}가지</b>: {_C('·'.join(fr.get('props',[])))}. "
                    "<b>그래서 목표가 바뀐다</b> → '이 3속성을 찾아 grid 를 만든다':")
        body.append(f"<div class='gnow'>goal = {html.escape((g.get('intent') or ''))}</div>")
        body.append("<span class='muted'>이 단계가 있어야, 다음 비교가 *왜 속성별*인지가 선다. "
                    "그리고 3속성을 이미 알기에 — 다음 비교는 grid 통째 *원시비교를 건너뛰고* 곧장 "
                    "속성별(특정범위·원소고정) 비교로 간다.</span>")
    elif kind == "apply" and op == "frame-object":
        fr = s["frame"] or {}
        props = [p.replace("_of", "") for p in fr.get("props", [])]
        focus = [p.replace("_of", "") for p in fr.get("focus", [])]
        body.append("<b>관측 + 목표 구체화 (OBJECT)</b> — 선택한 객체의 property 구조는 "
                    f"<b>{len(props)}가지</b>({_C('·'.join(props))}). 전부 보지 않고 "
                    f"<b>선호(preference)</b> 상 앞선 {_C('·'.join(focus))} 의 *변화*를 먼저 찾는다.")
        body.append(f"<div class='gnow'>goal = {html.escape((g.get('intent') or ''))}</div>")
        body.append("<span class='muted'>역시 grid 통째 원시비교가 아니라, 객체 property 의 "
                    "*변화(입력→출력)*를 속성별로 본다.</span>")
    elif kind == "apply" and op == "compare-pairs":
        c = s["compared"] or {}
        body.append("<b>원시 비교</b> — 자유변수(test)와 형제(example)의 <code>roles</code>(역할 시그니처) "
                    "통째 비교. example=완전(input+output), test=output 빠짐 → "
                    f"verdict = <span class='{'ok' if c.get('verdict')=='COMM' else 'bad'}'>"
                    f"{c.get('verdict')}</span> (다른데 '어디가'는 아직 모름).")
    elif kind == "apply" and op == "localize":
        body.append("<b>비교 심화(localize)</b> — roles 를 이름정렬해 항목별 비교 → 빠진 역할 "
                    "<code>output</code> 으로 국소화. <b>need 생성</b> → 목표가 날카로워짐:")
        body.append(f"<div class='gnow'>need = {_need_str(g)}</div>")
    elif kind == "apply" and op == "search-dsl":
        ds = s["dsl_search"]
        req = (g.get("need") or {}).get("requires")
        if ds:
            body.append(f"<b>DSL 탐색(효과 매칭)</b> — requires={_C(req)} 를 해소하는 DSL: "
                        f"<span class='ok'>{_C(ds)}</span> (effect 가 매칭됨).")
        else:
            body.append(f"<b>DSL 탐색(효과 매칭)</b> — requires={_C(req)} → 결과 "
                        f"<span class='bad'>∅</span>. 이 효과를 내는 DSL 이 없음(roles 를 바꾸는 작용 부재).")
    elif kind == "apply" and op == "observe-siblings":
        gp = s["grid_props"]
        rows = []
        for k in ("size", "color", "contents"):
            v = gp[k]
            vd = v["verdict"]
            note = ""
            if k == "size" and vd == "DIFF":
                note = (f" → 관계 <span class='ok'>{v.get('relation')}</span>"
                        if v.get("relation") else " <span class='bad'>(미결정)</span>")
            elif vd == "COMM":
                note = " → 채택"
            else:
                note = " <span class='bad'>(출력끼리론 부족)</span>"
            rows.append(f"<tr><td>{k}</td><td class='{'ok' if vd=='COMM' else 'bad'}'>{vd}</td>"
                        f"<td>{note}</td></tr>")
        body.append("<b>특정범위·원소고정 비교</b> (원시 통째비교는 <i>생략</i> — frame 으로 3속성을 "
                    "이미 알기에). 범위 = 자유변수(Pa.output)의 <b>형제</b> = example <b>출력</b>들 "
                    "(원소고정: 역할=output), 이를 property 별로 비교 (편향: COMM→채택):")
        body.append("<table class='schema'><tr><th>property</th><th>verdict</th><th></th></tr>"
                    + "".join(rows) + "</table>")
    elif kind == "apply" and op in ("compose-grid", "compose-object"):
        body.append("<b>DSL 조합</b> — 결정된 값으로 씨앗 원자 <code>make_grid</code>(캔버스) + "
                    "<code>coloring</code>(셀)를 조합해 격자를 짓는다 → <code>roles.output</code> 채움 "
                    "→ 목표 <span class='ok'>achieved</span>.")
    elif kind == "apply" and op == "select-object":
        o = s["obj_sel"] or {}
        body.append("<b>객체 선택</b> — OBJECT 는 grid 픽셀의 *부분집합*이라, <b>왜 이 객체인지</b>를 "
                    f"이유로 남긴다: <span class='ok'>{html.escape(o.get('reason',''))}</span> "
                    f"(기준 <code>{o.get('by')}</code>, 후보 {o.get('count')}개).")
    elif kind == "apply" and op == "observe-change":
        sc = s["schema"] or {}
        rows = "".join(f"<tr><td>{k}</td><td>{binding_desc(v)}</td></tr>" for k, v in sc.items())
        body.append("<b>변화 비교 + anti-unify</b> (역시 통째 원시비교가 아니라, frame 이 짚은 "
                    "color·coordinate 의 <b>변화</b>를 본다) — 입력객체↔출력객체 변화를 *원자 조합*"
                    "(in_coord/grid_dims + offset, 또는 const/from_g0)으로 일반화. via=선택 이유:")
        body.append(f"<table class='schema'><tr><th>property</th><th>바인딩 (=왜 그렇게 결정?)</th></tr>{rows}</table>")
    elif kind == "impasse":
        body.append(f"<b>막힘(no-change impasse)</b> — {html.escape((g.get('reason') or ''))}. "
                    f"제안할 operator 없음 → substate push <b>{html.escape(op)}</b>.")
        if "→GRID" in op or op.endswith("GRID"):
            body.append("<div class='gnow'>하강이 효과를 <b>변신</b>: holds(grid) → requires(create,grid). "
                        "GRID 에선 이 효과를 내는 make_grid 가 잡힌다.</div>")
        if op.endswith("OBJECT"):
            body.append("<div class='gnow'>contents/color 가 출력끼리론 부족 → OBJECT 에서 "
                        "<b>변화(입력→출력)</b>로 결정.</div>")
    elif kind == "unwind":
        body.append(f"<b>복기(unwind)</b> — 하위목표 해소 → substate pop ({html.escape(op)}). "
                    "상위 need 가 채워져 목표 <span class='ok'>achieved</span> 로 전파 (하강의 거울상).")
    elif kind == "solved":
        body.append("<b>★ 해결</b> — 조립된 격자를 answer 로 기록.")
    elif kind == "enter":
        body.append(f"<b>진입</b> — {html.escape(op)}.")

    return head + "".join(f"<div class='cmp'>{b}</div>" for b in body) + "</div></div>"


# ── 문제 한 개 렌더 ─────────────────────────────────────────────────────
def render_task(d):
    out = [f'<h2 id="{d["id"]}">{d["id"]} '
           + (f'<span class="ok">✓ 정답</span>' if d["correct"] else '<span class="bad">✗</span>')
           + "</h2>"]

    # roles 요약
    rs = " · ".join(f"{rid}=" + ("완전(input+output)" if (i and o) else "불완전(input만)")
                    for rid, i, o, t in d["roles"])
    out.append(f'<p class="muted">pair roles: {html.escape(rs)} — example 는 완전, test 는 output 빠짐 '
               '(이게 PAIR 에서 "빠진 칸 = 자유변수" 발견의 근거).</p>')

    # pairs
    out.append('<div class="pairs">')
    for i, (gin, gout) in enumerate(d["grids"]["train"]):
        out.append(f'<div class="pair"><span class="cap">train{i} in→out</span>'
                   f'{grid_html(gin)}<span class="arr">→</span>{grid_html(gout)}</div>')
    for i, (gin, gt) in enumerate(d["grids"]["test"]):
        out.append(f'<div class="pair test"><span class="cap">test in→정답</span>'
                   f'{grid_html(gin)}<span class="arr">→</span>{grid_html(gt)}</div>')
    out.append("</div>")

    # 결정 사이클 흐름
    out.append("<h3>결정 사이클 흐름 (propose→select→apply→impasse→하강→복기)</h3>")
    for s in d["steps"]:
        out.append(render_step(s))

    # 산출
    out.append('<div class="pred"><b>산출(answer)</b> ')
    out.append(grid_html(d["answer"]))
    verdict_txt = "정답과 일치 ✓" if d["correct"] else "불일치 ✗"
    out.append(f' &nbsp; {verdict_txt}</div>')
    return "\n".join(out)


CSS = """
body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:980px;margin:24px auto;
  padding:0 16px;color:#1a1a1a;line-height:1.55}
h1{border-bottom:3px solid #333;padding-bottom:8px}
h2{margin-top:46px;border-top:2px solid #ccc;padding-top:20px}
h3{margin-top:22px;color:#333}
.ok{color:#1a7f37;font-weight:700}.bad{color:#c62828;font-weight:700}
.muted{color:#777;font-size:.92em}
table.grid{border-collapse:collapse;display:inline-block;vertical-align:middle;
  border:1px solid #555;background:#555}
table.grid td{width:13px;height:13px;border:1px solid #333}
.pairs{display:flex;flex-wrap:wrap;gap:18px;align-items:center;margin:14px 0 6px}
.pair{display:flex;align-items:center;gap:6px;position:relative;
  padding:8px;border:1px solid #eee;border-radius:6px}
.pair.test{border-color:#f0c040;background:#fffdf2}
.pair .cap{position:absolute;bottom:-16px;left:8px;font-size:.72em;color:#888}
.arr{font-size:20px;color:#888}
.step{display:flex;gap:12px;margin:8px 0;border-left:4px solid #ccc;padding:8px 12px;
  background:#fafafa;border-radius:0 6px 6px 0}
.step.decisive{border-left-color:#1a7f37;background:#f3faf4}
.step.impasse{border-left-color:#d4a017;background:#fdf9ef}
.step .lv{font-weight:700;min-width:64px;color:#444}
.flow{font-size:.9em;color:#555;margin:0 0 4px}
.cmp{margin:4px 0 0;padding:5px 9px;background:#f4f8ff;border-radius:5px;font-size:.94em}
.gnow{margin:4px 0 0;color:#a06000;background:#fff7e6;padding:4px 8px;border-radius:4px}
table.schema{border-collapse:collapse;margin:6px 0}
table.schema th,table.schema td{border:1px solid #ccc;padding:3px 9px;font-size:.9em;text-align:left}
table.schema th{background:#f0f0f0}
.pred{background:#f6f6f6;padding:12px;border-radius:6px;margin-top:10px}
code{background:#eef;padding:1px 4px;border-radius:3px;font-size:.92em}
.legend{background:#f0f4ff;padding:14px 18px;border-radius:8px;font-size:.94em;margin:14px 0}
.legend table{border-collapse:collapse;margin:8px 0}
.legend td{border:1px solid #cdd;padding:3px 10px;font-size:.92em}
nav a{margin-right:12px;font-weight:600}
"""

INTRO = """
<p>이 문서는 ARBOR 가 easy000a~i 를 <b>SOAR 결정 사이클</b>로 푸는 전 과정을 <b>매 사이클</b>
풀어 적은 해설서다. 새 로직이 아니라, 상태에 따라 불려오는 <b>단위 행동(operator)</b>들의
조합이다.</p>
<div class="legend">
<b>불변 루프</b> — 모든 레벨(TASK→PAIR→GRID→OBJECT)에서 같다. 단 *매 단계가 늘 도는 건 아니다* —
상태에 따라 어떤 단위 행동은 <i>생략</i>된다:
<div style="margin:6px 0"><b>관측+목표구체화(frame)</b>: 한 노드를 관측 → 그 계층의 property 개수를 알고
목표를 "그 속성들을 찾는다"로 구체화 →
[원시(통째) 비교] → (어디가 안 보임=막힘) → 비교 심화(localize) → need
→ 효과로 DSL 탐색 → 있으면 apply / 없으면 impasse → 하강(holds 가 효과를 변신) → … → 복기(unwind)</div>
<span class="muted">예: PAIR 은 원시비교로 '빠진 역할'을 발견하지만, GRID·OBJECT 는 frame 이 속성을
짚어줘 <b>원시(통째)비교를 건너뛰고</b> 곧장 속성별(특정범위·원소고정) 비교로 간다.</span>
<br><b>편향</b>: COMM=그대로 채택(미지가 공통에 순응) / DIFF=어긋남(같게 or 하강). &nbsp;
<b>자유변수</b>: example=고정(앎) / test 슬롯=만들 것.
<table>
<tr><td>깊이 들어가기(하강)</td><td>impasse→push_substate</td><td>S1→S2→S3→S4 = TASK→PAIR→GRID→OBJECT</td></tr>
<tr><td>원시 비교</td><td>compare (통째)</td><td>COMM/DIFF</td></tr>
<tr><td>비교 심화</td><td>localize (이름정렬)</td><td>'어디가' 국소화 → need</td></tr>
<tr><td>범위·원소고정 비교</td><td>select+compare</td><td>형제(example 출력) 비교</td></tr>
<tr><td>다름 완화 DSL 찾기</td><td>find_by_effect</td><td>효과 매칭(계층 아님)</td></tr>
<tr><td>DSL 조합</td><td>make_grid + coloring</td><td>씨앗 원자 조합</td></tr>
</table>
<b>SOAR 대응</b>: propose(WM 조건 매칭) → select → apply(WM 변경) → no-change impasse → substate → 복기.
</div>
"""


def main():
    data = [solve_with_trace(t) for t in TASKS]
    nav = " ".join(f'<a href="#{d["id"]}">{d["id"][-1]}{"✓" if d["correct"] else "✗"}</a>'
                   for d in data)
    n_ok = sum(d["correct"] for d in data)
    parts = [f"<!doctype html><html lang=ko><head><meta charset=utf-8>"
             f"<title>ARBOR 결정 사이클 해설서 (easy000a~i)</title><style>{CSS}</style></head><body>"]
    parts.append("<h1>ARBOR 결정 사이클 해설서 — easy000a~i</h1>")
    parts.append(f"<p><b>{n_ok}/9</b> 정답. <nav>{nav}</nav></p>")
    parts.append(INTRO)
    for d in data:
        parts.append(render_task(d))
    parts.append("</body></html>")

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "solutions_decision.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"wrote {out}  ({n_ok}/9 정답)")


if __name__ == "__main__":
    main()
