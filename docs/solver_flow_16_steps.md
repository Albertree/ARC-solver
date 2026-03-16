# 솔버 16단계 흐름 (문제 풀기 시작 이후)

에이전트·환경 정의 후 **문제를 받아 풀기 시작한 뒤**의 단계별 흐름.  
저장 위치는 `semantic_memory/`(= MEMORY_ROOT) 기준.

---

## 1. 문제 수신 및 TASK 해석

- **의미**: 문제를 받아 ARCKG 방식으로 해석한다. TASK만 보고 “무엇을 어떻게 해야 하는지”를 생각한다.
- **코드**: `ARCManager.from_hex_code(task_id)` → `TASK`, `example_pairs`, `test_pairs`.
- **저장**: 아직 없음.

---

## 2. TASK property 확인

- **의미**: TASK의 property를 확인한다.
- **코드**: `task.update_property()` → `example_pair_count`, `test_pair_count` 등.
- **저장**: (선택) `task.to_json()` → `semantic_memory/N_T{task_id}/E_T{task_id}.json`.

---

## 3. Semantic memory 내 다른 TASK의 property와 비교

- **의미**: 다른 TASK의 property와 비교한다. **처음 상태라면 이 단계는 없다.**
- **저장**: 비교가 수행되면 `semantic_memory/` 아래 비교 결과 JSON 생성 (예: `E_T{hex1}-T{hex2}.json`).
- **구현**: 현재는 생략. 추후 semantic memory에 다른 TASK가 있으면 비교 후 저장.

---

## 4. 깊은 탐색 시작 (PAIR 레벨로)

- **의미**: TASK property만으로는 목표를 달성할 만한 정보가 없어 PAIR 레벨 탐색을 시작한다.
- **코드**: 목표 설정 전제; 다음 단계(5–6)에서 PAIR property·비교 후 목표를 세움.

---

## 5. PAIR 레벨: 모든 PAIR의 property 확인

- **의미**: example PAIR들과 test PAIR(Pa, Pb, …) 모두의 property를 확인한다.
- **코드**: 각 `pair.update_property()` → `grid_count` 등. (필요 시 `pair.to_json()`.)
- **저장**: (선택) `semantic_memory/N_T{task_id}/N_P{pair_id}/E_P{pair_id}.json` (PAIR별 self-edge).

---

## 6. PAIR들 비교 → 목표 설정

- **의미**: PAIR들을 비교하고, 그 결과를 바탕으로 목표를 세운다.  
  예: test pair(Pa)의 grid_count=1, example들은 2 → “Pa의 grid_count를 2로 만든다”.
- **저장**: 비교 결과는 **N_T{task_id}/** 아래.  
  - PAIR 간 GRID 비교: `N_T{task_id}/E_{label1}-{label2}.json` (예: `E_P0G0-P1G0.json`).  
  - PAIR–PAIR 비교(있을 경우): `N_T{task_id}/E_P{p1}-P{p2}.json`.
- **코드**: `_compare_grids_across_pairs()` 등으로 PAIR 간 그리드 비교 후, 결과를 보고 목표 설정 (예: `goal = "create_missing_grid"` 등).

---

## 7. 한 PAIR 선택 후 GRID 단위: property 확인 및 G0 vs G1 비교

- **의미**: 하나의 example PAIR을 선택해, 그 안의 두 GRID(G0, G1)의 property를 확인하고, 두 GRID를 비교한다.  
  이때 “GRID가 어떻게 구성되는지”를 처음으로 파악한다.
- **저장**: **N_P{pair_num}/** 아래.  
  - GRID property: `N_T{task_id}/N_P{p}/N_G{g}/E_G{g}.json`.  
  - G0 vs G1 비교: `N_T{task_id}/N_P{p}/E_G0-G1.json` (LCA가 PAIR이므로 N_P{p} 아래).
- **코드**: `_ensure_grid_property(grid)`, `compare(pair.input_grid, pair.output_grid, save=True)` (경로는 LCA로 N_P{p}에 저장).

---

## 8. 목표 전환: grid_count → grid generate (size, color, contents)

- **의미**: “grid_count를 2로 만든다”에서 “grid를 생성한다”로 목표가 바뀐다.  
  필요한 정보: `grid.size`, `grid.color`, `grid.contents`.
- **코드**: 내부 상태/목표 변수 갱신. `_try_make_grid_from_property(pair)` 등으로 property만으로 생성 가능 여부 판단.

---

## 9. 한 PAIR 내 G0–G1만으로는 Pa 예측 불가 → 다른 PAIR의 GRID 보기

- **의미**: 한 PAIR 내 두 GRID 비교만으로는 test PAIR(Pa)의 출력을 예측할 수 없으므로, 다른 example PAIR의 GRID를 본다.
- **저장**: 이미 6에서 PAIR 간 GRID 비교가 N_T{task_id}/ 아래 되어 있음.
- **코드**: `_compare_grids_across_pairs()`에서 example 간·example–test 간 그리드 비교 수행.

---

## 10. 두 번째 example PAIR의 GRID property·비교 → size/color 예측, contents 목표

- **의미**: 두 번째 example PAIR에서도 GRID property를 확인하고 비교한다.  
  모든 grid.size가 같다, input_grid끼리 color 같다, output_grid끼리 color 같다 등으로  
  test output의 **size·color**는 예측하고, **contents**는 예측 불가로 두고 목표로 남긴다.
- **저장**: N_T 아래 PAIR 간 GRID 비교 결과 활용. (이미 6·9에서 저장.)
- **코드**: `_predict_test_g1()` 등에서 size/color/contents 동일 여부 판단 후, 불완전하면 “grid.contents 예측”을 다음 목표로 설정.

---

## 11. OBJECT 레벨: 한 GRID 내 객체 property 확인 및 같은 그리드 내 객체끼리 비교

- **의미**: 첫 example PAIR의 GRID0에 대해 모든 object의 property를 확인하고, **같은 그리드 내** object끼리 비교한다.  
  이어서 GRID1에 대해서도 동일하게 한다.
- **저장**: **G_0, G_1**에 해당.  
  - `semantic_memory/N_T{task_id}/N_P{p}/N_G0/` 아래 같은 그리드 내 object 비교: `E_*O{i}-O{j}.json`.  
  - `N_P{p}/N_G1/` 아래 동일.
- **코드**: 각 grid의 `objects`에 대해 `compare(obj_i, obj_j, save=True)` (같은 grid 내만).  
  LCA가 GRID이면 `id_pair_to_comparison_path` → `N_P{p}/N_G{g}/` 아래 저장.

---

## 12. 한 PAIR 내 G0 객체 vs G1 객체 비교 → P_{0} 저장, 프로그램 시도

- **의미**: 같은 PAIR 안에서 GRID0의 object들과 GRID1의 object들을 쌍으로 비교한다 (예: 7×7=49).  
  score가 높은 순으로 관련 객체 매핑.  
  “G0의 어떤 속성 객체가 G1에서 어떤 속성으로 바뀌는지”를 파악하고, 이 정보로 **규칙 기반 프로그램**을 만들어 input grid에 실행해 output이 나오는지 확인한다.  
  나오면 더 깊은 탐색 불필요; 아니면 더 깊은 탐색.
- **저장**: **P_{0}** = `N_T{task_id}/N_P0/` 아래.  
  - G0 object vs G1 object 비교는 LCA가 PAIR → `N_P0/E_P0G0O{i}-P0G1O{j}.json`.
- **코드**: `for obj0 in grid0.objects: for obj1 in grid1.objects: compare(obj0, obj1, save=True)` (label 없이 하면 LCA=PAIR → N_P0).  
  비교 결과로 프로그램 생성·실행 후 성공 여부에 따라 13으로 넘어가거나 14 이하로.

---

## 13. 11–12를 다음 example PAIR에 대해 반복

- **의미**: 두 번째 example PAIR에 대해서도 11(같은 그리드 내 object 비교 → G_0, G_1 해당 폴더), 12(같은 PAIR 내 G0–G1 object 비교 → P_{1} 등)를 수행한다.
- **저장**: `N_P1/` 아래 N_G0, N_G1, 및 PAIR 내 cross-grid object 비교.

---

## 14. 두 PAIR의 grid 변화를 하나의 공통 변화로: 객체 비교·강제 링크, N_T 저장

- **의미**: pair0과 pair1에서 모은 정보의 공통점을 찾는다.  
  “변화했던 객체” 중 하나를 골라, 다른 pair의 객체와 비교한다.  
  표면적 property가 아니라 **관계(relation) 유사성**으로 대응을 찾고 (예: P0G0 area=9 color=5 ↔ P1G0 area=8 color=5),  
  test처럼 **input_grid만 있는 경우**에도 이 링크를 input_grid 안에서만 찾을 수 있도록 한다.  
  비교 결과는 **N_T{task_id}/** 아래 저장.
- **저장**: `semantic_memory/N_T{task_id}/` 아래 PAIR 간·객체 간 비교 JSON (예: `E_P0G0O{i}-P1G0O{j}.json`).
- **코드**: `_compare_pair_components(pair0, pair1, 0, 1)` 등.  
  이미 `compare(o0, o1, save=True, label1=..., label2=...)`로 N_T 아래 저장됨.

---

## 15. 링크된 두 객체에 대한 깊은 탐색: DIFF 깊이 분석

- **의미**: “이 둘을 이어야 한다”는 목표가 정해진 뒤, 두 객체가 포함된 비교 결과들을 보고,  
  **DIFF를 깊게** 파고든다 (pixel 레벨이 아니라 comparison 결과의 DIFF).  
  area, coord, shape 등 다른 property들을 분석해 **공통점**을 끌어낸다 (예: 같은 색 객체들과의 비교에서 area가 모두 gt).  
  이 정보로 그리드 **안**의 정보만으로 객체 선택·변화 규칙을 정할 수 있게 한다.
- **저장**: 기존 `*_diff_ordering` 등 DIFF 깊이 분석 결과 (WM found 또는 semantic_memory 내 적절한 경로).
- **코드**: `deepen_diff_ordering`(예: `ARCKG.diff_deepen`) 등으로 relation_1_* / relation_2_* 에 대해 ordering 추출.

---

## 16. 이어진 정보 → 프로그램 → test input 실행 → test output .contents

- **의미**: 14–15에서 얻은 “이어진 정보”를 프로그램으로 변환하고, test input에 실행한 결과를 test output grid의 **.contents**로 한다.
- **코드**: 프로그램 생성·실행 후 `_test_output_predictions` 등에 반영.  
  환경에 제출할 답은 이 결과로 채움.

---

## 저장 위치 요약

| 단계 | 내용 | 저장 위치 (semantic_memory/ 기준) |
|------|------|-----------------------------------|
| 2 | TASK property | N_T{task_id}/E_T{task_id}.json |
| 3 | (처음엔 없음) 다른 TASK와 비교 | semantic_memory/ 아래 비교 JSON |
| 5 | PAIR property | N_T{task_id}/N_P{pair_id}/E_P{pair_id}.json |
| 6 | PAIR들 비교 | N_T{task_id}/E_{label1}-{label2}.json, E_P{p1}-P{p2}.json 등 |
| 7 | 한 PAIR 내 G0–G1 비교 | N_T{task_id}/N_P{p}/E_G0-G1.json |
| 11 | 같은 그리드 내 object 비교 | N_T{task_id}/N_P{p}/N_G0/, N_G1/ 아래 E_*O{i}-O{j}.json |
| 12 | 한 PAIR 내 G0 object vs G1 object | N_T{task_id}/N_P{p}/E_P{p}G0O{i}-P{p}G1O{j}.json |
| 14 | PAIR 간 object 비교 | N_T{task_id}/E_P0G0O{i}-P1G0O{j}.json 등 |

이 순서대로 코드가 동작하도록 **`ARCSolver.run_solver_flow_16_steps()`** 드라이버를 두었다.

- **SOAR 연산자**: `USE_FLOW_16=1`(기본)이면 `effect_submit_answer`에서 `run_solver_flow_16_steps()`를 호출한다. `USE_FLOW_16=0`이면 기존처럼 `_compare_grids_across_pairs()` + `_predict_test_g1()`만 호출한다.
- **직접 실행**: `python run_flow_16.py [task_id]` 로 16단계 흐름만 실행해 볼 수 있다.
