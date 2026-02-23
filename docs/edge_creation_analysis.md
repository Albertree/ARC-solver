# Edge(E_*.json) 생성 시점 분석

## 요약

| 구분 | 생성 시점 | 대략 개수 | 생성 위치(코드) |
|------|------------|------------|------------------|
| **Property 엣지** (E_T, E_P, E_G, E_O, E_X 단일) | **초기 data load** | ~7,000+ | 각 component `to_json()` (TASK/PAIR/GRID/OBJECT/PIXEL) |
| **Comparison 엣지** (E_*-* 형식) | **문제 해결 단계** (pair-specific solution) | ~41,000+ | `compare(..., save=True)` → `save_comparison_result()` |

- **대부분의 E_* 파일**은 초기 로드가 아니라 **문제 해결 과정(arc_solver)**에서 생성된 **comparison 엣지**입니다.
- 초기 로드에서는 **property 엣지**만 생성됩니다 (노드당 1개: E_T, E_P, E_G, E_O, E_X).

---

## 1. 초기 data load 단계에서 생성되는 것 (Property)

**호출 경로:** `ARCManager.from_hex_code()` → `TASK.from_json()` → 각 노드의 `from_json()` 끝에서 `to_json()` 호출

| 파일 패턴 | 의미 | 생성 위치 |
|-----------|------|------------|
| `E_T{hex}.json` | TASK property | `task.py` `to_json()` |
| `E_P{id}.json` | PAIR property | `pair.py` `to_json()` |
| `E_G{id}.json` | GRID property | `grid.py` `to_json()` (id 0,1만) |
| `E_O{id}.json` | OBJECT property | `object.py` `to_json()` |
| `E_X{id}.json` | PIXEL property | `pixel.py` `to_json()` (그리드 직속 + 객체 소속) |

- 한 task에 pair 2개, grid 2개, object 수십 개, pixel 수백~수천 개면 **property만으로도 수천 개**의 E_* 파일이 생깁니다.
- 현재 memory 기준: E_T 16, E_P 32, E_G 96, E_O 481, **E_X 48,481** → 그중 **property만** 있는 건 E_X 기준 약 7,000개 수준으로 추정 (나머지 E_X는 아래 comparison과 이름 겹침으로 함께 집계됨).

---

## 2. 문제 해결 단계에서 생성되는 것 (Comparison, 선택적이어야 함)

**호출 경로:** `workers/arc_solver.py` → `compare(comp1, comp2, save=True)` → `save_comparison_result()` → `id_pair_to_comparison_path()` 로 경로 결정 후 저장

| 단계 | 코드 위치 | 호출 예 | 생성 파일 예 |
|------|------------|----------|----------------|
| GRID | `arc_solver.py` L54 | `compare(pair.input_grid, pair.output_grid, save=True)` | `E_G0-G1.json` (pair당 1개) |
| OBJECT | `arc_solver.py` L111 | `for obj_i, obj_o: compare(obj_i, obj_o, save=True)` | `E_O0-O1.json` 등 (객체 쌍마다) |
| PIXEL | `arc_solver.py` L183 | `for pix_i, pix_o: compare(pix_i, pix_o, save=True)` | `E_X27-X4.json` 등 (픽셀 쌍마다) |
| OBJECT–OBJECT (매핑) | `arc_solver.py` L152, L333 | `compare(obj1, obj2, save=True)` | `E_O*-O*.json` |

- **PIXEL 단계**: `object_result.pixels` × `output_grid.pixels` 이중 루프로 **모든 픽셀 쌍**에 대해 `compare(..., save=True)` → 수만 개의 `E_X*-X*.json` comparison 파일 생성.
- 현재 memory에서 **이름에 `-`가 들어가는 comparison 엣지**가 **약 41,792개**로 집계됨.

즉, “엄청 많이 생성된 edge”의 상당수는 **초기 로드가 아니라, pair별 solution 생성하면서 GRID/OBJECT/PIXEL 비교를 할 때** 생긴 **comparison 엣지**입니다.

---

## 3. 설계 의도와의 관계

- **의도:** “EDGE는 후에 필요에 따라 **선택적으로** component가 선택되었을 때만 형성.”
- **현재 동작:**
  - **Property:** 초기 로드 시 **모든** TASK/PAIR/GRID/OBJECT/PIXEL에 대해 무조건 `to_json()` → E_T, E_P, E_G, E_O, E_X 생성.
  - **Comparison:** 문제 해결 시 **비교한 모든 쌍**에 대해 `save=True`로 전부 저장 (특히 PIXEL 이중 루프로 인해 수만 개 생성).

따라서 “선택적으로만 생성”하려면:

1. **Property**
   - 초기 로드에서 `to_json()` 호출을 제거하거나,
   - “선택된” 노드에 대해서만 property E_*를 쓰도록 조건을 두는 방식으로 변경이 필요할 수 있음.
2. **Comparison**
   - `compare(..., save=True)`를 기본이 아니라 **필요할 때만** 호출하거나,
   - “선택된 component”에 대해서만 `save_comparison_result()`를 호출하도록 바꾸는 것이 필요합니다.

---

## 4. 참고: comparison 저장 여부

- `compare(comp1, comp2, save=True)` → 항상 `id_pair_to_comparison_path()` 경로에 저장.
- `compare(..., save=False)` → 메모리만 반환, 파일 미생성.  
  현재 `program_gen/manager.py`, `program_gen/rules.py`에서는 `save=False` 사용.

요약하면, **지금 많이 쌓인 edge들은 대부분 “초기 로드”가 아니라 “문제 해결 시 pair별로 GRID/OBJECT/PIXEL 비교할 때 생성된 comparison 엣지”**이고, 설계 의도대로라면 이 부분을 선택적으로만 저장하도록 바꾸는 게 맞습니다.
