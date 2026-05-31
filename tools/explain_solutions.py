"""
풀이 해설서 생성기 — easy000a~i 를 *실제 솔버로* 풀며 단계마다 무엇을·왜 했는지
기록해 HTML(solutions.html)로 낸다.

담는 것: 받은 격자 / 레벨별 흐름(막힘·우선순위·고정 구분) / 비교한 범위·결과 /
탐색 시도(성공·실패 이유) / 모듈·args 출처 / 최종 예측·정답.

실행: python tools/explain_solutions.py   → solutions.html
"""

import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import program.search as search
from managers.arc_manager import ARCManager
from agent.wm import WorkingMemory
from agent.descent import descend_to_decisive
from agent.predict import predict

TASKS = [f"easy000{c}" for c in "abcdefghi"]

PALETTE = {0: "#111", 1: "#0074D9", 2: "#FF4136", 3: "#2ECC40", 4: "#FFDC00",
           5: "#AAAAAA", 6: "#F012BE", 7: "#FF851B", 8: "#7FDBFF", 9: "#870C25"}


def grid_html(raw):
    if raw is None:
        return '<span class="muted">(숨김/예측대상)</span>'
    rows = "".join(
        "<tr>" + "".join(
            f'<td style="background:{PALETTE.get(v, "#fff")}"></td>' for v in row) + "</tr>"
        for row in raw)
    return f'<table class="grid">{rows}</table>'


def solve_with_trace(task_id):
    """한 문제를 실제 솔버로 풀며 레벨 흐름 + 탐색 시도 + 예측을 수집."""
    mgr = ARCManager(data_root="data")
    task = mgr.load_task(task_id)
    gt = mgr.test_ground_truth(task_id)

    levels = []
    search.TRACE = []
    wm = WorkingMemory()
    result, gs = descend_to_decisive(
        wm, task, on_level=lambda lv, g, r: levels.append((lv, g, r)))
    attempts = list(search.TRACE)
    search.TRACE = None

    answer = predict(result["evidence"]) if result["decisive"] else None
    grids = {
        "train": [(p.input_grid.raw, p.output_grid.raw) for p in task.example_pairs],
        "test": [(p.input_grid.raw, gt[i]) for i, p in enumerate(task.test_pairs)],
    }
    return {"id": task_id, "grids": grids, "levels": levels, "attempts": attempts,
            "result": result, "answer": answer, "correct": bool(gt) and answer == gt[0]}


def _short(v, n=44):
    s = str(v)
    return html.escape(s if len(s) <= n else s[:n] + " …")


def render_receipt(receipt, depth=2):
    """comparison receipt 를 per-property COMM/DIFF·점수로 (긴 값은 … 후략)."""
    def rr(r, d):
        t, sc = r.get("type"), r.get("score")
        head = (f'<span class="{ "ok" if t == "COMM" else "bad" }">{t}</span>'
                + (f' <span class="muted">({sc})</span>' if sc else ""))
        cat = r.get("category")
        if isinstance(cat, dict) and d > 0:
            items = [(k, v) for k, v in cat.items() if isinstance(v, dict)]
            shown = items[:6]
            lis = "".join(f'<li><code>{html.escape(str(k))}</code>: {rr(v, d - 1)}</li>' for k, v in shown)
            more = (f'<li class="muted">… ({len(items) - len(shown)}개 더)</li>'
                    if len(items) > len(shown) else "")
            return head + f'<ul class="rec">{lis}{more}</ul>'
        if "comp1" in r:
            return head + f' <span class="muted">[{_short(r.get("comp1"))} | {_short(r.get("comp2"))}]</span>'
        return head
    return rr(receipt["result"], depth)


_TAG_LABEL = {"observe": "관측", "compare": "비교", "goal": "목표변경", "decide": "판단"}


def render_task(d):
    h = [f'<section><h2 id="{d["id"]}">{d["id"]} '
         f'<span class="{ "ok" if d["correct"] else "bad" }">'
         f'{"정답 ✓" if d["correct"] else "오답 ✗"}</span></h2>']

    # 1) 문제
    h.append('<h3>1. 받은 문제</h3><div class="pairs">')
    for gi, go in d["grids"]["train"]:
        h.append(f'<div class="pair">{grid_html(gi)}<span class="arr">→</span>{grid_html(go)}'
                 f'<div class="cap">example</div></div>')
    for gi, go in d["grids"]["test"]:
        h.append(f'<div class="pair test">{grid_html(gi)}<span class="arr">→</span>{grid_html(go)}'
                 f'<div class="cap">test (출력=예측대상)</div></div>')
    h.append('</div>')

    # 2) 풀이 흐름 — 레벨별, phase(관측·비교·목표변경) 단위. 목표는 관측-주도로 진화.
    h.append('<h3>2. 풀이 흐름 (막혀야 내려간다 · 목표는 관측 때마다 진화)</h3>')
    fixed = "레벨 순서(TASK→PAIR→GRID→OBJECT)는 <b>코드 고정</b>; 내려가는 <b>시점</b>은 막힘(impasse)."
    for li, (lv, goal, r) in enumerate(d["levels"]):
        cls = "decisive" if r["decisive"] else "impasse"
        note = fixed if li == 0 else "이전 레벨에서 <b>막혀</b> 내려옴 (강제 ✗)."
        h.append(f'<div class="step {cls}"><div class="lv">[{lv}]</div><div class="body">'
                 f'<div class="flow">{note}</div><ol class="phases">')
        for p in r["phases"]:
            tag = p["tag"]
            badge = f'<span class="tag t-{tag}">{_TAG_LABEL.get(tag, tag)}</span>'
            line = f'<li class="ph-{tag}">{badge} {p["desc"]}'
            if tag == "goal":
                line += f'<div class="gnow">→ 목표: <b>{html.escape(p["goal"])}</b></div>'
            for la, lb, rec in p["compares"]:
                line += (f'<div class="cmp">compare(<code>{la}</code>, <code>{lb}</code>) = '
                         f'{render_receipt(rec)}</div>')
            # OBJECT 의 anti-unify(decide) phase 뒤에 property 탐색 상세 붙이기
            if lv == "OBJECT" and tag == "decide" and d["attempts"]:
                line += '<div class="search"><b>property 탐색 (우선순위대로, 첫 적합 채택)</b>'
                cur = None
                for a in d["attempts"]:
                    if a["prop"] != cur:
                        if cur is not None:
                            line += '</ul>'
                        line += f'<div class="prop">▶ <code>{a["prop"]}</code></div><ul>'
                        cur = a["prop"]
                    mark = '<span class="ok">✓ 채택</span>' if a["ok"] else '<span class="bad">✗</span>'
                    line += (f'<li>{mark} {html.escape(a["attempt"])} — '
                             f'<span class="muted">{html.escape(a["detail"])}</span></li>')
                line += '</ul></div>'
            h.append(line + '</li>')
        v = ("<b class='ok'>결정적 → 멈춤</b>" if r["decisive"]
             else "<b class='impasse'>막힘 → 더 깊이</b>")
        h.append(f'</ol><div class="decide">{v} <span class="muted">({html.escape(r["reason"])})</span>'
                 f'</div></div></div>')

    # 3) 찾은 규칙(schema) + 예측
    ev = d["result"].get("evidence") or {}
    if "schema" in ev:
        h.append('<h3>3. 찾은 규칙 (schema = 출력 property 별 조합)</h3><table class="schema"><tr>'
                 '<th>property</th><th>조합(kind / via)</th><th>의미</th></tr>')
        meaning = {"from_g0": "입력에서 그대로", "const": "고정값",
                   "in_coord+Δ": "입력 위치 + 이동", "grid_dims+Δ": "grid 크기 기준(모서리 등)"}
        for k, v in ev["schema"].items():
            via = v.get("via", v["kind"])
            extra = f" offset={v['offset']}" if v.get("offset") else ""
            h.append(f'<tr><td><code>{k}</code></td><td>{via}{extra}</td>'
                     f'<td>{meaning.get(via, v["kind"])}</td></tr>')
        h.append('</table>')
        h.append('<h3>4. 예측 (씨앗 조합: make_grid + coloring)</h3>'
                 f'<div class="pred">make_grid(size={ev["size"]}) → 빈 격자, '
                 f'그 위에 coloring(위치={ev["cells"]}, 색={ev["color"]})<br>'
                 '<span class="muted">args 출처: size·위치·색 = 위 schema 를 test 입력에 적용해 푼 값</span>'
                 f'<div class="pairs"><div class="pair">{grid_html(d["answer"])}'
                 '<div class="cap">제출한 답</div></div></div></div>')
    else:
        h.append('<h3>3. 찾은 규칙 + 예측</h3><div class="pred">'
                 'GRID 에서 <b>모든 example 출력(G1)이 COMM(동일)</b> → 그 공통 grid 를 그대로 제출 '
                 '(Slice 1 메커니즘, 출력 고정).'
                 f'<div class="pairs"><div class="pair">{grid_html(d["answer"])}'
                 '<div class="cap">제출한 답</div></div></div></div>')
    h.append('</section>')
    return "\n".join(h)


CSS = """
body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:960px;margin:24px auto;
  padding:0 16px;color:#1a1a1a;line-height:1.55}
h1{border-bottom:3px solid #333;padding-bottom:8px}
h2{margin-top:44px;border-top:2px solid #ccc;padding-top:20px}
.ok{color:#1a7f37;font-weight:700}.bad{color:#c62828;font-weight:700}
.impasse{color:#b8860b}.muted{color:#777;font-size:.92em}
table.grid{border-collapse:collapse;display:inline-block;vertical-align:middle;
  border:1px solid #555;background:#555}
table.grid td{width:13px;height:13px;border:1px solid #333}
.pairs{display:flex;flex-wrap:wrap;gap:18px;align-items:center;margin:10px 0}
.pair{display:flex;align-items:center;gap:6px;flex-direction:row;position:relative;
  padding:8px;border:1px solid #eee;border-radius:6px}
.pair.test{border-color:#f0c040;background:#fffdf2}
.pair .cap{position:absolute;bottom:-16px;left:8px;font-size:.72em;color:#888}
.arr{font-size:20px;color:#888}
.step{display:flex;gap:12px;margin:10px 0;border-left:4px solid #ccc;padding:8px 12px;
  background:#fafafa;border-radius:0 6px 6px 0}
.step.decisive{border-left-color:#1a7f37;background:#f3faf4}
.step.impasse{border-left-color:#d4a017;background:#fdf9ef}
.step .lv{font-weight:700;min-width:64px;color:#444}
.flow{font-size:.9em;color:#666;margin:2px 0 6px}
ol.phases{margin:4px 0;padding-left:22px}
ol.phases>li{margin:5px 0;font-size:.93em}
li.ph-goal{background:#fff7e6;border-left:3px solid #e0a000;padding:3px 8px;list-style:none;margin-left:-22px}
li.ph-compare{padding:2px 0}
.tag{font-size:.72em;padding:1px 6px;border-radius:9px;margin-right:5px;vertical-align:middle;color:#fff}
.t-observe{background:#9aa}.t-compare{background:#3b6}.t-goal{background:#e0a000}.t-decide{background:#789}
.gnow{margin:3px 0 0 4px;color:#a06000}
.cmp{margin:4px 0 4px 8px;padding:4px 8px;background:#f4f8ff;border-radius:5px;font-size:.95em}
ul.rec{margin:2px 0;padding-left:18px;list-style:none}
ul.rec>li{margin:1px 0;font-size:.95em}
.search{margin:6px 0;padding:8px;background:#eef3ff;border-radius:6px}
.search ul{margin:3px 0 6px;padding-left:18px}.search li{font-size:.9em}
.prop{font-weight:600;margin-top:4px}
.decide{margin-top:8px;font-weight:600}
table.schema{border-collapse:collapse;margin:8px 0}
table.schema th,table.schema td{border:1px solid #ccc;padding:4px 10px;font-size:.92em;text-align:left}
table.schema th{background:#f0f0f0}
.pred{background:#f6f6f6;padding:12px;border-radius:6px}
code{background:#eef;padding:1px 4px;border-radius:3px}
.legend{background:#f0f4ff;padding:12px 16px;border-radius:8px;font-size:.93em}
nav a{margin-right:10px}
"""


def main():
    data = [solve_with_trace(t) for t in TASKS]
    n_ok = sum(d["correct"] for d in data)
    nav = " ".join(f'<a href="#{d["id"]}">{d["id"][-1]}</a>' for d in data)
    body = "\n".join(render_task(d) for d in data)
    doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>ARBOR 풀이 해설서 (easy000a~i)</title><style>{CSS}</style></head><body>
<h1>ARBOR 풀이 해설서 — easy000a~i ({n_ok}/{len(data)})</h1>
<div class="legend"><b>읽는 법</b> — 흐름 성격 3종:
<span class="muted">① <b>고정</b>: 코드로 정해진 순서(레벨 TASK→PAIR→GRID→OBJECT).
② <b>막힘(impasse)</b>: 현 레벨에서 결정 못 해서 더 깊이 내려감(P1, 강제 ✗).
③ <b>우선순위 탐색</b>: OBJECT 에서 property 마다 가까운 조합부터 시도, 첫 적합 채택.</span><br>
색칠 박스(왼쪽 테두리): <span class="ok">초록=결정적</span> / <span class="impasse">노랑=막힘</span>.
</div>
<nav>바로가기: {nav}</nav>
{body}
</body></html>"""
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "solutions.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"생성: {out}  ({n_ok}/{len(data)} 정답)")


if __name__ == "__main__":
    main()
