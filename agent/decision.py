"""
decision (SOAR 결정 사이클) — **WM 을 읽어 다음 진행을 결정** 한다.

SOAR 그대로, 매 사이클:
  propose : WM 조건에 맞는 operator 들을 제안   (read WM)
  select  : 그 중 하나 선택 (지금은 단일 제안 → tie 없음)
  apply   : operator 적용 → WM 변경            (write WM)
제안이 없음(quiescence)인데 목표가 미충족이면 → **no-change impasse → 하강(substate)**.

operator 들은 우리의 *진짜* 연산자: compare(통째 비교) · localize(비교 심화) · search-dsl.
전부 WM 을 읽고/쓴다 — 제어가 파이썬 지역변수가 아니라 *WM 상태* 로 걸린다.
"""

from agent.goal import Goal, Need, deposit_goal
from agent.goal_stack import next_level
from procedural_memory.DSL.relation import compare, verdict, localize
from procedural_memory.DSL.selection import select
from procedural_memory.DSL.util import is_foreground
from procedural_memory.DSL.effect import effect
from procedural_memory.DSL.registry import body, SPECS
from procedural_memory.dsl_search import find_by_effect
from program.anti_unification import anti_unify_objects, is_solvable
from program.search import resolve_property


# ── WM 읽기 헬퍼 (조건은 전부 WM 에서 읽는다) ────────────────────────────
def _goal(wm):
    return wm.active.get("goal")


def _need(wm):
    g = wm.active.get("goal") or {}
    return g.get("need")


def _update_goal(wm, **changes):
    """WM 의 goal 을 갱신(재대입 → S1 은 timetag 기록, substate 는 live dict)."""
    g = dict(wm.active.get("goal") or {})
    g.update(changes)
    wm.active["goal"] = g


def _stack_find(wm, key):
    """상위 substate 들에서 key 를 찾는다 (예: GRID 가 결정한 grid-props 를 OBJECT 가 읽음)."""
    for s in reversed([wm.s1] + wm._substate_stack):
        if key in s:
            return s[key]
    return None


def _level_props(node_type):
    """그 계층 노드의 property 목록을 *property DSL 명세*에서 읽는다.
    grid → [size,color,contents], object → 8개. (계층의 property 구조 = 무엇을 찾을지.)"""
    return [n for n, s in SPECS.items()
            if s["kind"] == "property" and s["in"] == [node_type]]


def _pair_pair(task):
    """비교 대상: 완전한 example 하나 vs 불완전한 test."""
    return task.example_pairs[0], task.test_pairs[0]


def _cmp_name(n):
    """비교 로그용 짧은 노드 이름 (task 접두 제거)."""
    nid = getattr(n, "node_id", None) or str(n)
    parts = nid.split(".")
    return ".".join(parts[1:]) if len(parts) > 1 else nid


def _log_compare(wm, receipts):
    """각 (x,y) pair × attr 비교를 WME 로 WM 에 남긴다 — RAM→WM (SOAR 충실, grain=가).
    receipts = compare() 결과 [(x, y, receipt), ...]. wm.active["comparisons"] 에 누적 →
    *무엇↔무엇을 어느 attr 로 비교해 COMM/DIFF* 가 WM 에서 보임 (매 반복 대상이 바뀌는 것도)."""
    log = wm.active.setdefault("comparisons", [])
    for x, y, rec in receipts:
        cat = (rec.get("result") or {}).get("category", {})
        for attr, v in cat.items():
            if not isinstance(v, dict):
                continue
            log.append({"i": len(log) + 1, "left": _cmp_name(x), "right": _cmp_name(y),
                        "attr": attr, "result": v.get("type")})


# ── operator 정의: 각자 propose(조건, read WM) + apply(효과, write WM) ────
def _prop_compare(wm, task):
    # 목표는 있는데 아직 통째 비교를 안 했다
    return _goal(wm) is not None and "compared" not in wm.active

def _apply_compare(wm, task):
    P0, Pa = _pair_pair(task)
    wm.load_node(P0); wm.load_node(Pa)             # 방문 = 폴더 열기 → 노드 속성 WM 적재 (lazy)
    recs = compare([P0], [Pa])
    _log_compare(wm, recs)                          # 비교 → WM (attr별 한 줄)
    rec = recs[0][2]
    wm.active["compared"] = {"verdict": verdict(rec)[0],
                             "ref": P0.node_id, "cur": Pa.node_id}


def _prop_localize(wm, task):
    # 통째 비교가 DIFF 인데 '어디가' 아직 모름(need 없음) → 심화
    return (wm.active.get("compared", {}).get("verdict") == "DIFF"
            and _need(wm) is None)

def _apply_localize(wm, task):
    P0, Pa = _pair_pair(task)
    r0, ra = wm.find_node(P0.node_id), wm.find_node(Pa.node_id)   # roles = WM record 의 property
    attr, (have, want) = next(iter(localize(r0["roles"], ra["roles"]).items()))
    need = Need(Pa, f"roles.{attr}", have, want,
                requires=effect("add", "roles"), holds="grid")
    _update_goal(wm, intent="Pa 의 빠진 output 채우기", need=need.to_wme())


def _prop_search(wm, task):
    # need 가 국소화됐는데 아직 DSL 탐색을 안 했다
    return _need(wm) is not None and "dsl-search" not in wm.active

def _apply_search(wm, task):
    cands = find_by_effect(_need(wm)["requires"])
    wm.active["dsl-search"] = [c["name"] for c in cands]


# ── GRID operator: 단위 행동들의 인스턴스 ────────────────────────────────
# frame: 하강 직후 *한 grid 를 관측* → grid 는 3속성(size·color·contents) → 목표가
# "3속성을 찾아 grid 를 만든다"로 구체화. (이게 있어야 다음 비교가 *왜* 속성별인지 선다.)
# observe (frame): **단일 골격 + variant 별 관측 커널** (scope-driven, compose 와 같은 꼴).
# 골격은 "관측 결과 = frame WME + goal intent" 로 동일 — 다른 건 *무엇을 관측해 어떤
# props 를 프레임에 담나*뿐이라 그 부분만 커널로 분리한다. 커널 → (observed, props, focus, intent).
def _observe(wm, task, frame_of):
    observed, props, focus, intent = frame_of(wm, task)   # variant 별 관측 커널 (적재 포함)
    frame = {"observed": observed, "level": wm.active["level"], "props": props}
    if focus:
        frame["focus"] = focus                            # 선호 초점 (OBJECT 만)
    wm.active["frame"] = frame
    _update_goal(wm, intent=intent)


def _prop_observe_task(wm, task):
    # TASK 진입 직후 — task 노드 관측 (아직 frame 없음)
    return wm.active.get("level") == "TASK" and "frame" not in wm.active

def _frame_task(wm, task):
    """TASK 커널: task 노드를 관측. props 는 roles (배선 시그니처) — 아직 task-property
    로 등록 안 돼 명시 지정(roles-as-task-property 화는 Q1 조건 일반화 때)."""
    wm.load_node(task)                                     # 방문 = task 노드 폴더 열기
    return task.node_id, ["roles"], None, "task 관측 — test 의 빠진 출력을 채운다"


def _prop_frame(wm, task):
    n = _need(wm)
    return (wm.active.get("level") == "GRID" and n is not None
            and n.get("requires", {}).get("kind") == "grid" and "frame" not in wm.active)

def _frame_grid(wm, task):
    """GRID 커널: 대표 grid(P0.G0) 를 관측. props 는 그 계층 property 구조에서 읽음."""
    rep = task.example_pairs[0].input_grid                 # P0.G0 (대표 grid 관측)
    wm.load_node(rep)                                      # 방문 = 폴더 열기 (대표 grid 적재)
    props = _level_props("grid")                           # [size, color, contents]
    return (rep.node_id, props, None,
            "grid 의 " + str(len(props)) + "속성(" + "·".join(props) + ")을 찾아 grid 를 만든다")

# 특정 범위·원소 고정 비교: 자유변수(Pa.output)의 형제 = example 출력들을
# property 별로 비교(편향 COMM→채택 / DIFF→하강). frame 으로 3속성을 알았으니
# *원시(통째) 비교는 건너뛰고* 바로 속성별 비교로 간다.
def _prop_observe(wm, task):
    n = _need(wm)
    return (n is not None and n.get("requires", {}).get("kind") == "grid"
            and "frame" in wm.active and "grid-props" not in wm.active)

def _determine_size(wm, task):
    """make_grid 의 size 인자 결정 (편향: 같음→채택):
       출력끼리 COMM → 상수값.  DIFF 면 입력과의 관계(출력크기=입력크기)면 from-input.
       size 사실은 *WM 에 적재된 노드* 에서 읽는다 (find_node).
    """
    osz = [wm.find_node(p.output_grid.node_id)["size"] for p in task.example_pairs]
    isz = [wm.find_node(p.input_grid.node_id)["size"]  for p in task.example_pairs]
    if all(s == osz[0] for s in osz):
        return {"verdict": "COMM", "value": osz[0], "relation": None}
    if all(o == i for o, i in zip(osz, isz)):                  # 변화: 크기 보존
        return {"verdict": "DIFF", "value": None, "relation": "from-input"}
    return {"verdict": "DIFF", "value": None, "relation": None}

def _apply_observe(wm, task):
    # 방문: 형제 비교에 쓸 입력·출력 grid 들을 WM 에 적재 (size 판정이 입력 size 도 읽음)
    for p in task.example_pairs:
        wm.load_node(p.input_grid); wm.load_node(p.output_grid)
    outs = [p.output_grid for p in task.example_pairs]          # 형제(완전한 known)
    recs = compare(outs, outs)                                  # 형제 출력 pairwise 비교
    _log_compare(wm, recs)                                      # 비교 → WM (pair×attr별 한 줄)
    comm = verdict(recs[0][2])[2]                              # 원시 비교 → COMM 키
    out0 = wm.find_node(outs[0].node_id)                       # 공통값은 *WM 노드* 에서 읽음
    props = {}
    for k in ("color", "contents"):
        is_comm = k in comm
        props[k] = {"verdict": "COMM" if is_comm else "DIFF",
                    "value": out0[k] if is_comm else None}      # COMM → 공통값 채택 (WM)
    props["size"] = _determine_size(wm, task)                   # size 는 make_grid 인자 — 관계까지 본다
    wm.active["grid-props"] = props


# DSL 조합 (compose): **단일 골격(level-agnostic) + variant 별 셀 추출 커널**.
# 골격(size 결정·캔버스·칠하기·achieve)은 GRID/OBJECT 동일 — 다른 건 오직 (bg, painted)
# 의 *출처*다. 그래서 제어흐름은 하나로 두고, 진짜 다른 데이터 추출만 커널로 분리한다
# (scope-driven 단일 apply: 손코딩 level 분기 → 데이터 커널). painted = [((r,c), color), …].
def _size_resolved(sz):
    return sz["verdict"] == "COMM" or sz.get("relation") == "from-input"

def _prop_compose(wm, task):
    gp = wm.active.get("grid-props")
    if not gp or "built-grid" in wm.active:
        return False
    cells_ok = gp["color"]["verdict"] == "COMM" and gp["contents"]["verdict"] == "COMM"
    return (_size_resolved(gp["size"]) and cells_ok          # size 는 관계로 풀려도 OK
            and "make_grid" in (wm.active.get("dsl-search") or []))

def _cells_from_grid_props(wm, task):
    """GRID 커널: 결정된 contents 에서 배경(최다색)과 칠할 셀들을 뽑는다 (상수)."""
    contents_v = _stack_find(wm, "grid-props")["contents"]["value"]
    flat = [c for row in contents_v for c in row]
    bg = max(set(flat), key=flat.count)                        # 배경 = 최다 색
    painted = [((r, c), v) for r, row in enumerate(contents_v)
               for c, v in enumerate(row) if v != bg]          # 비배경 셀 = 원래 색
    return bg, painted, "make_grid+coloring 조립 → roles.output 채움"

def _cells_from_change(wm, task):
    """OBJECT 커널: 변화 schema 를 test input 에 resolve → fgcolor·셀들 (test 의존)."""
    schema = wm.active["change-schema"]
    test = _obj_ctx(task.test_pairs[0].input_grid)             # ★ test input 만으로 선택+변형
    color_set = resolve_property(schema["color"], test)
    fgcolor = next(k for k, v in color_set.items() if v and k != 0)
    cells = resolve_property(schema["coordinate"], test)       # [[r,c]]
    painted = [((r, c), fgcolor) for r, c in cells]            # 변화로 결정한 셀 = fgcolor
    return 0, painted, "변화 schema 를 test input 에 적용 → 격자 조립"

def _apply_compose(wm, task, cells):
    """단일 조립 골격 — 커널 `cells` 가 준 (bg, painted) 로 캔버스를 칠해 built-grid.
    size 는 양쪽 동일: COMM 상수값 or test 입력 크기 (둘 다 WM 노드에서 읽음)."""
    test_gid = wm.load_node(task.test_pairs[0].input_grid)    # 방문: test 입력 grid → node id
    bg, painted, reason = cells(wm, task)                      # variant 별 셀 추출 커널
    sz = _stack_find(wm, "grid-props")["size"]                 # size 사실은 GRID 가 이미 결정
    size_v = sz["value"] if sz["verdict"] == "COMM" else wm.find_node(test_gid)["size"]
    mk, col = body("make_grid"), body("coloring")
    grid = mk(size_v, fill=bg)                                 # 캔버스 (atom 1)
    for (r, c), color in painted:
        grid = col(grid, (r, c), color)                       # 셀 칠하기 (atom 2 조합)
    wm.active["built-grid"] = grid
    _update_goal(wm, status="achieved", reason=reason)


# ── OBJECT operator: grid 픽셀의 *부분집합*이라 더 복잡 — *왜 그 객체를 골랐는지*를
#    이유로 남기고, 변화(입력→출력)를 비교해 객체 color·coordinate 를 일반화한다.
_fg = lambda g: select(g, "object", is_foreground)[0]          # 전경 객체 (선택 단위행동)

def _obj_ctx(grid):
    """anti-unify 입력 맥락: 전경 객체의 color·coordinate + grid 치수(좌표 base 용)."""
    o = _fg(grid).to_json()
    gs = grid.to_json()["size"]
    return {"color": o["color"], "coordinate": o["coordinate"],
            "grid_h": gs["height"], "grid_w": gs["width"]}

def _prop_select_obj(wm, task):
    return wm.active.get("level") == "OBJECT" and "object-selection" not in wm.active

def _apply_select_obj(wm, task):
    # *왜 이 객체인가* 를 기록: 전경(배경≠0) 객체, 후보 수로 유일/선호 판단
    wm.load_node(task.example_pairs[0].input_grid)             # 방문: 객체를 담은 grid 폴더
    cands = select(task.example_pairs[0].input_grid, "object", is_foreground)
    for o in cands:
        wm.load_node(o)                                       # 방문한 후보 객체만 적재
    reason = (f"전경(배경 0 아님) 객체 {len(cands)}개 → 유일하므로 선택"
              if len(cands) == 1 else
              f"전경 객체 {len(cands)}개 → 선호순(color…) 첫 객체 선택")
    wm.active["object-selection"] = {"by": "is_foreground", "count": len(cands), "reason": reason}

def _prop_frame_obj(wm, task):
    return (wm.active.get("level") == "OBJECT"
            and "object-selection" in wm.active and "frame" not in wm.active)

def _frame_obj(wm, task):
    """OBJECT 커널: 이미 select 한 전경객체를 관측 (적재 없음). focus = 선호 초점."""
    props = _level_props("object")                         # 8속성
    return ("전경객체", props, ["color_of", "coordinate_of"],
            "객체는 " + str(len(props)) + "속성 — 선호상 color·coordinate 의 변화(입력→출력)를 찾는다")

def _prop_observe_change(wm, task):
    return (wm.active.get("level") == "OBJECT" and "object-selection" in wm.active
            and "frame" in wm.active and "change-schema" not in wm.active)

def _apply_observe_change(wm, task):
    # 변화(입력→출력) 비교 → 각 property 를 atom 조합으로 일반화 (anti-unify)
    for p in task.example_pairs:
        wm.load_node(p.input_grid); wm.load_node(p.output_grid)   # 방문: 변화 비교할 grid 들
    examples = [(_obj_ctx(p.input_grid), _obj_ctx(p.output_grid)) for p in task.example_pairs]
    schema = anti_unify_objects(examples, ["color", "coordinate"])
    wm.active["change-schema"] = schema                        # binding(=via 이유 포함)

def _prop_compose_obj(wm, task):
    sch = wm.active.get("change-schema")
    return (wm.active.get("level") == "OBJECT" and sch is not None
            and is_solvable(sch) and "built-grid" not in wm.active)
    # apply = 공통 _apply_compose + _cells_from_change 커널 (GENERAL_OPS 에서 결합)


# 일반 operator — 기능적·level-agnostic 이름. 계층/대상은 args, 선택은 조건(variant)으로.
# (→ wiki arbor-operators). 같은 일반 op 가 level 별 variant 로 분기:
#   compare = pairs(원시)/roles(localize)/siblings(범위)  ·  observe = grid/object frame  …
# variant = (propose 조건, apply, 그 조건이 유효한 level). variant 조건이 sequencing 을 보장하므로
# 일반 op 의 순서(선호)는 단일 후보 보장 시 무관 — observe→select→compare→search→generalize→compose.
# (현재는 조건이 *아직 level 을 참조* — 진짜 level-agnostic(need-shape) 화는 다음 단계.)
GENERAL_OPS = [
    # observe: 같은 골격(_observe), variant 는 관측 커널만 다름 (scope-driven).
    {"name": "observe",    "variants": [
        (_prop_observe_task, lambda wm, t: _observe(wm, t, _frame_task), "TASK"),
        (_prop_frame,        lambda wm, t: _observe(wm, t, _frame_grid), "GRID"),
        (_prop_frame_obj,    lambda wm, t: _observe(wm, t, _frame_obj), "OBJECT")]},
    {"name": "select",     "variants": [(_prop_select_obj, _apply_select_obj, "OBJECT")]},
    {"name": "compare",    "variants": [(_prop_compare, _apply_compare, "PAIR"),
                                        (_prop_localize, _apply_localize, "PAIR"),
                                        (_prop_observe, _apply_observe, "GRID")]},
    {"name": "search",     "variants": [(_prop_search, _apply_search, "PAIR"),
                                        (_prop_search, _apply_search, "GRID")]},
    {"name": "generalize", "variants": [(_prop_observe_change, _apply_observe_change, "OBJECT")]},
    # compose: 같은 골격(_apply_compose), variant 는 셀 추출 커널만 다름 (scope-driven).
    {"name": "compose",    "variants": [
        (_prop_compose,     lambda wm, t: _apply_compose(wm, t, _cells_from_grid_props), "GRID"),
        (_prop_compose_obj, lambda wm, t: _apply_compose(wm, t, _cells_from_change),     "OBJECT")]},
]

_LEVELS_WITH_OPS = {lvl for g in GENERAL_OPS for (_, _, lvl) in g["variants"]}


# ── 결정 사이클 ──────────────────────────────────────────────────────────
def run(wm, task, on_step=None, max_steps=30):
    """WM 을 읽어 propose→select→apply, 막히면 impasse→하강. (GRID 진입에서 멈춤.)"""
    for step in range(max_steps):
        level = wm.active.get("level")
        # 일반 op 후보: variant 조건이 (현 level 에서) 맞는 op. 선택 = 순서(선호).
        cands = []                                 # [(general_op, apply)]
        for g in GENERAL_OPS:
            for cond, apply, lvl in g["variants"]:
                if lvl == level and cond(wm, task):
                    cands.append((g, apply))
                    break                          # op 당 첫 매칭 variant
        if cands:
            g, apply = cands[0]                    # select (선호=순서; 단일 후보면 tie 없음)
            apply(wm, task)                        # apply → WM 변경
            if on_step:
                on_step(step, "apply", g["name"], [c[0]["name"] for c in cands], wm)

            # 복기(unwind): 목표 달성 → 스택 거슬러 상위 need 해소 (하강의 거울상)
            if (_goal(wm) or {}).get("status") == "achieved":
                answer = wm.active.get("built-grid")
                schema = wm.active.get("change-schema")      # 학습 재적재용(semantic 성장) — pop 전에 보존
                while wm._substate_stack:
                    wm.pop_substate()
                    if _goal(wm) is not None:
                        _update_goal(wm, status="achieved", reason="하위목표 해소 → 복기")
                    if on_step:
                        on_step(step, "unwind", f"pop → {wm.active.get('level')}", [], wm)
                wm.s1["answer"] = answer
                wm.s1["answer-schema"] = schema
                if on_step:
                    on_step(step, "solved", "answer 기록", [], wm)
                return "solved"
            continue

        # quiescence — 제안 없음
        g = _goal(wm)
        unmet = g is not None and g.get("status") != "achieved"
        nxt = next_level(level)
        if not unmet or nxt is None:
            if on_step:
                on_step(step, "halt", level, [], wm)
            return f"halt@{level}"

        # no-change impasse → 하강
        gp = wm.active.get("grid-props")
        if gp:                                              # GRID: make_grid 는 잡혔고 인자가 미결정
            undet = [k for k, v in gp.items()
                     if v["verdict"] == "DIFF" and not v.get("relation")]
            reason = f"{undet} 미결정 (출력끼리론 부족) → 변화 탐색 필요"
        elif "dsl-search" in wm.active:
            reason = f"no activatable DSL @{level}"
        else:
            reason = f"no operator @{level}"
        if _need(wm) is not None:
            _update_goal(wm, status="blocked", reason=reason)
        if on_step:
            on_step(step, "impasse", f"{level}→{nxt}", [], wm)

        parent_need = _need(wm)
        wm.push_substate("no-change", "operator")
        wm.active["level"] = nxt
        child = Goal(f"{nxt} 에서 해소", scope=nxt)
        if parent_need and parent_need.get("holds"):
            # GRID 진입: 하강이 효과를 *변신* — holds(grid) → requires(create, grid)
            child.intent = f"{parent_need['holds']} 를 지어 {parent_need['attr']} 채우기"
            child.sharpen(Need(parent_need["target"], parent_need["attr"], None,
                               parent_need["holds"], effect("create", parent_need["holds"])))
        elif nxt == "OBJECT" and gp:
            # OBJECT 진입: GRID 에서 못 푼 셀(color·coordinate)을 *변화* 로 결정
            undet = [k for k, v in gp.items() if v["verdict"] == "DIFF" and not v.get("relation")]
            child.intent = "변화(입력→출력)로 객체 " + "·".join(undet) + " 결정"
            child.sharpen(Need("output", "object." + ",".join(undet), None, "from-change",
                               effect("determine", "change")))
        deposit_goal(wm, child)
        if on_step:
            on_step(step, "descend", f"{level}→{nxt}", [], wm)   # substate push = 타임스텝

        if nxt not in _LEVELS_WITH_OPS:
            if on_step:
                on_step(step, "enter", f"{nxt} (operator 미구현 — 다음 모듈)", [], wm)
            return f"entered@{nxt}"
    return "max-steps"
