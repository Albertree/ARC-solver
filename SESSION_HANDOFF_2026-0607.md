# ARBOR 작업 핸드오프 — 2026-06-06 ~ 06-07

> 다른 세션에서 맥락을 이어가기 위한 문서. 맨 아래 §8 에 직전 대화 마지막 출력을 그대로 붙였다.
> 작업 레포: `~/Desktop/ARC-solver` · 위키: `~/Desktop/wiki` (Karpathy LLM-wiki 패턴).

---

## 0. 한 줄 요약

이 세션은 **(a) ARBOR 의 SOAR 충실 흐름을 위키에 정립**하고, **(b) 코드를 "모든 지식이 WM 에 있고 operator 가 WM 에서 읽는" 구조로 재작성**했으며, **(c) process_visualizer 를 디버거형 대시보드로 재설계**하고, **(d) operator 를 계층-specific(11) → 일반(9) 으로 재편**했다. 내내 easy000a–i **9/9 유지**.

## 1. ARBOR 이란 / 핵심 원칙

- **ARBOR** = SOAR 인지 아키텍처 + 5계층 ARCKG 로 ARC 를 푸는 순수 기호 시스템. 풀이는 evidence 일 뿐 목표는 *의도대로(관계·기호·bottom-up·self-extending) 자라는 에이전트*.
- **통제는 WM 상태에 있다** (프로그램 카운터 없음). operator 가 WM 을 읽어(propose) 선택(decide)·적용(apply).
- **검색 대상 = 변환 T**(격자 아님), training pair = 검증 **오라클**. (목표지만 코드는 아직 격자 조립.)
- **ARCKG = 영속화된 WM** (SOAR semantic 아님). load=page-in, flush=page-out(lazy).

## 2. 이 세션에서 한 일 (시간순)

1. **process_visualizer step/substep 재설계** — read-first, 각 step 머리에 WM 상태(view) 타일. step=WM 변화 상태, substep=그 상태에서 시작하는 사이클.
2. **SOAR 충실 흐름 정립(위키)** — 사이클 I/O 경계, i-support/o-support, 내부 vs 외부 operator, **substate=오프라인 상상**(`^io` top-only), impasse 타입(tie/conflict/constraint-failure/no-change), 검색대상=T·training=오라클. **정정**: TASK→PIXEL 자동 descent 는 architecture 아님(impasse 타입으로 emergent) → `next_level` 제거 대상.
3. **ARC-AGI-2 retry** — 제출↔맞/틀↔재시도(≤3). "틀림"=**reject preference** → 랭킹된 가설 다음 후보. **무확률 다양화**. retry 의미 = training underdetermination.
4. **impasse 해결 체계(위키)** — impasse 에서 substate 가 열려 실행되는 게 한 종류=**substate operator** {계층하강·원시/조건/선택 비교·변환탐색·args탐색}. 풀이 단계 = **gather→synthesize→generalize**(program synthesis arc), 전이 트리거=**need-shape**.
5. **외부 구조 완성(코드, step 1)** — `ActiveSoarAgent.solve` 를 `agent/decision.py::run` 으로 승격(구 `descend_to_decisive` 는 스캐폴드). 환경(`arc2_env`)↔agent↔retry: 같은 task 재호출=직전 답 "틀림" → `_rejected` 누적 → `wm.s1["rejected"]` 주입. visualizer 가 같은 경로 추적.
6. **ARCKG→WM lazy 적재(코드, step 1~4)**:
   - `wm.load_node(node)` / `wm.find_node(id)` — 노드(속성+엣지)를 WM 에 WME 로.
   - input 이 TASK 노드 적재 / **방문 시** 노드 적재(폴더 모델, operator 가 만질 때).
   - operator 가 facts 를 **WM 에서** 읽음(size·color·contents·roles → `find_node`). 비교는 `^comparisons` WME 로 기록.
   - 계산 엔진(compare/select/anti-unify)은 I/O 가 WM 에 묶임(내부는 객체 읽되 같은 데이터).
7. **roles property(코드)** — pair/task to_json 을 `grid_count`/개수 → **`roles` presence-dict**(input/output·example/test)로. "무엇이 빠졌나" 보존. compare-pairs 가 roles 로 비교.
8. **visualizer 재설계** — narrative(글 많아 *기각*) → **dashboard.html**: ① WM(고정 근거·접이트리) + ② 결정(토큰·색·op→결과, 문장0, substep별 점진 노출) + ③ 격자 + 목표스택(별도) + 하단 타임라인. impasse 는 decide 에서만, 후보 열거, +/−/~ 고정칸.
9. **일반 operator(위키+코드)** — 11 level-op → **9 일반 op**(compare/observe/select/search/generalize/compose + descend/submit). 계층/대상=args, 선택=precondition+preference. 위키 `arbor-operators` 신규.
10. **TASK op** — `observe-task`(실제 op, TASK 진입 시 관측) 추가 + impasse match 에 descend 후보 노출.

## 3. 현재 코드 상태 (파일별)

- `agent/decision.py` — **핵심 엔진**. `GENERAL_OPS`(observe/select/compare/search/generalize/compose, 각 level-variant) + `_prop_*`/`_apply_*`. `run()` = 후보(조건 매칭)→첫 후보 선택→apply; 후보 0 ∧ goal 미충족 → impasse → `descend`(impasse 분기, 아직 propose 루프 밖); achieve→unwind→solved. operator 가 `wm.find_node` 로 WM 읽음. `_log_compare` 로 비교 WME. `observe-task`.
- `agent/active_agent.py` — `solve(task, on_step=None)`: WM 만들고 inject→루트목표→rejected 주입→`decision_run`→`s1["answer"]`→emit. 같은 task 재호출 시 직전 답 reject 누적.
- `agent/wm.py` — `load_node`/`find_node`/`_active_id`. ARCKG 노드를 `active["arckg"]` 에 적재.
- `agent/io.py` — `inject_arc_task` 가 `wm.load_node(task)` (TASK 노드 적재).
- `agent/goal.py` — `Goal{intent,status(OPEN/BLOCKED/ACHIEVED),need,...}`, `Need`, `deposit_goal`.
- `ARCKG/pair.py`·`task.py` — `to_json` = `{roles:{...}}` (grid_count/개수 대체).
- `procedural_memory/DSL/property/__init__.py` — `roles` = `to_json["roles"]`; `grid_count`/`pair_count` 는 파생.
- 검증: `python run.py --task ARC_easy_a/easy000a … --out-dir none` → **9/9**.

## 4. 비주얼라이저 (`process_visualizer/`)

- `tracer.py` — `build_trace(repo, task_id)`: `decision.run` 추적 → step/substep 구조. substep phase: input·view·match·propose·preference·select·compute·apply·descend·unwind·solved. 마커: goals·compared·comparisons·grid_props·dsl_search·frame·obj_sel·schema·match(스캔표)·built. **GENERAL_OPS import.**
- `generate.py` — easy000a–i 풀어 `data.js` 생성. (`cd process_visualizer && python generate.py`)
- **`dashboard.html`** — *현재 메인 뷰*. WM 고정 + 결정 토큰 + 목표스택 + 격자 + 타임라인.
- `index.html` — 구 5패널 뷰(참고용). `narrative.html` — 서사 실험(기각, 참고용).
- 표시 원칙: **토큰·색·`op→결과`·표, 문장 최소, 디테일 호버**. WM 접이 트리(color 기본 접힘).

## 5. 핵심 설계 결정 (요약)

- WM = 모든 의사결정의 근거(고정). 지식·비교·노드 전부 WM WME.
- ARCKG = 영속 WM, lazy load/flush.
- operator = 일반 기능, 계층/대상=args, 선택=precondition+preference. "args 찾기"=operator(select·search·generalize·resolve).
- 비교 종류(원시/고정/범위) = `compare` + scope(select).
- impasse = decide 에서; 해결법 = substate operator(현재 descend 만 구현).
- property 두 계층: 실체(grid/object)=셀 측정 · 구조(task/pair)=배선(roles) 측정.

## 6. 로드맵 / 미완 (deferred — 한 덩어리의 SOAR 정렬)

1. **조건 level-agnostic 화** — 각 op 에 need-shape 조건 충분히 → variant/level 참조 제거.
2. **descend·submit 정식 op 승격** — propose 루프로. (descend 가 apply 중 level 변경 → tracer level 귀속 처리 필요.)
3. **scope-driven 단일 apply** — compare/observe/compose 의 grid/object variant 통합.
4. **ranked preference + `rejected` 소비** — `_apply_observe`·`_determine_size` 의 "COMM→채택" hard 편향 → runner-up 보존; retry 가 다른 답.
5. **tie 평가 substate** — 후보 변환을 training 오라클로 검증(best).
6. **`next_level` 고정 하강 제거** — 깊이 emergent; 검색대상=변환 T.
7. **semantic flush** — 풀이 끝에 WM→ARCKG(disk) 물질화(학습/영속).
8. visualizer: descend/submit 정식화 반영, dashboard 다듬기.

## 7. 위키 포인터 (`~/Desktop/wiki/wiki/`)

- `arbor.md` — 시스템 허브 + 2026-06 정정 절.
- `arbor-operators.md` — **9 일반 operator 스펙**(args·의존그래프·선택흐름·11→9 매핑).
- `arbor-execution-trace.md` — 11 모듈 + 단계형 시나리오 + 일반-op 재편 callout + roles 코드반영.
- `impasse.md` — impasse 타입 + substate operator 해결 체계 + 정정(계층하강≠architecture).
- `preference.md` — decide 슬롯, reject-preference 무확률 retry.
- `soar.md` — 사이클 I/O·i/o-support·내부vs외부 op·substate=상상.
- `arc-agi.md` — 3회 피드백 루프 평가.
- `arbor-open-questions.md` — Q-A~E 누적(need-shape 경첩 등).
- raw: `claude-arbor-soar-flow-io-impasse-retry-2026-06-06`, `claude-arbor-impasse-resolution-substate-operators-2026-06-06`, `claude-arbor-decision-cycle-operators-visualizer-2026-06-07`, `claude-arbor-general-operators-2026-06-07`.

## 8. 직전 대화 마지막 출력 (verbatim)

> 사용자 질문: (1) 조건이 적어 level 참조하는 것 맞나? (2) descend·submit 은 왜 아직 제안 op 아닌가? (3) variant 분기는 어디서? + TASK 단계에도 제안 op(observe·descend) 추가 요청.

**됐어 — 9/9 유지, TASK에 observe(실제 op) + descend(해결법 후보) 노출:**

```
step0 (big0)  observe 사이클 — op=observe, match=[observe✓]   ← TASK 의 실제 제안 op
step1 (big1)  impasse 사이클 — match=[observe✗, descend✓]     ← descend 가 후보로 보임
              → select impasse → descend ↓PAIR
```

- **observe-task** = 진짜 op (TASK 진입 시 task 노드 관측 → frame). TASK가 더 이상 "0개" 아님.
- **descend** = impasse match에 해결법 후보(✓)로 노출.
- step0 view엔 여전히 wm-init(씨앗 green) 보이고, op=observe로 "주입된 task를 관측".

### 정직하게 — descend/submit의 현 상태
- **descend는 *표시상* 후보로 떴지만 코드상으론 아직 impasse 해결(propose 루프 밖)이야.** 진짜 propose-op 승격은 *apply 중 level이 바뀌어 tracer level 귀속이 꼬이는* 문제 때문에 보류 — 별도로 신중히 해야 함(Q2 답).
- **submit도 아직 achieve 핸들러**(터미널). 승격 가능, 후속.
- **variant 분기(Q3)** 는 apply 코드가 level-specific이라 남음 — scope-driven 단일 apply로 가면 사라짐(진짜 일반화, 후속).

### Q 답 요약
- **Q1**: 맞음 — 조건이 빈약해 level 참조 중. 진짜 일반화 = 각 op 에 need-shape 조건 충분히.
- **Q2**: descend=impasse→substate(아키텍처 응답), submit=achieve→emit(터미널) 으로 *특수 제어흐름*에 둠. 승격 가능하나 impasse 표현·tracer level 귀속 영향.
- **Q3**: variant = 기존 11 level-op 를 일반 이름으로 묶으며 생김(apply 코드가 level별로 손코딩). scope-driven 단일 apply 면 사라짐.

→ 다음 한 덩어리: **조건 일반화(Q1) + descend/submit 정식 승격(Q2) + scope-driven 통합(Q3) = 진짜 SOAR 정렬.**
