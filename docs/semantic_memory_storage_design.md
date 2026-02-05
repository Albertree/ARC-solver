# Semantic Memory 저장 구조 설계 (5층 + 파일 명명)

`memory_structure.txt`와 현재 코드 기준으로, **이론적 5개 층**에 맞추어 폴더 깊이를 줄이고, **파일 이름만으로 노드/엣지·타입을 구분**할 수 있게 정리한 제안입니다.

---

## 1. 현재 구조 (실질 10층, 중간에 node/edge 분류)

현재 경로는 대략 다음과 같습니다.

- **노드(객체 속성)**  
  `memory / TASK_nodes / TASK_{hex} / TASK_property / TASK_{hex}_property.json`  
  → 깊이: root + TASK_nodes + TASK_hex + **TASK_property** + 파일 = 5단계만 가도 파일 하나.

- **실제 최대 깊이** (예: OBJECT 아래 PIXEL)  
  `memory / TASK_nodes / TASK_{hex} / PAIR_nodes / PAIR_{p} / GRID_nodes / GRID_{g} / OBJECT_nodes / OBJECT_{o} / PIXEL_nodes / PIXEL_{x} / PIXEL_property / PIXEL_{x}_property.json`  
  → **실질 10개 폴더 층** (memory 제외하면 9층).

여기서 **“중간 층”**은 다음처럼 **노드/엣지 구분용**입니다.

- `*_nodes/` — 해당 타입의 노드들이 들어가는 컨테이너
- `*_property/` — 그 노드의 속성 JSON 하나만 넣는 폴더
- `*_edges/` — 비교 결과(엣지) JSON들을 넣는 폴더 (+ GRID/OBJECT/PIXEL, score 등 하위 분류)

즉, **엔티티 계층(TASK→PAIR→GRID→OBJECT/PIXEL)**은 5개인데, 각 단계마다 `_nodes` / `_property` / `_edges` 같은 **분류용 폴더**가 붙어서 층 수가 늘어난 상태입니다.

---

## 2. 목표: 이론적 5개 층만 쓰기

**엔티티 계층만** 5개로 두고, “노드 vs 엣지”와 “타입”은 **폴더 이름 + 파일 이름**으로 표현하는 방식입니다.

- **층 1** (root): `memory/`
- **층 2**: 태스크 = `memory/{task_hex}/`
- **층 3**: 페어 = `memory/{task_hex}/pair_{p}/`
- **층 4**: 그리드 = `memory/{task_hex}/pair_{p}/grid_{g}/`
- **층 5**: 객체/픽셀 = `memory/.../grid_{g}/object_{o}/` 또는 `.../grid_{g}/pixel_{x}/`

OBJECT 아래 PIXEL을 두면 층이 6이 되므로, **“5층”을 엄격히 지키려면** OBJECT와 PIXEL을 모두 grid 직속으로 두는 방식(형제 관계)을 권장합니다.  
필요 시 `grid_{g}/object_{o}/pixel_{x}/`를 쓰면 6층이 됩니다.

---

## 3. 제안 폴더 구조 (5층 + 엣지 보관 방식)

```
memory/
└── {task_hex}/                    # 층 2: 태스크
    ├── node.json                  # TASK 노드 1개 (property)
    ├── pair_{p}/                  # 층 3: 페어
    │   ├── node.json              # PAIR 노드 1개
    │   ├── edges/                 # 이 페어 소속 비교 결과 (PAIR/GRID)
    │   │   ├── PAIR/
    │   │   │   └── {score}/
    │   │   │       └── PAIR_{p1}-{p2}.json
    │   │   └── GRID/
    │   │       └── {score}/
    │   │           └── GRID_{g1}-{g2}.json
    │   └── grid_{g}/              # 층 4: 그리드
    │       ├── node.json          # GRID 노드 1개
    │       ├── edges/            # 이 그리드 소속 비교 (OBJECT/PIXEL)
    │       │   ├── OBJECT/
    │       │   │   └── {score}/
    │       │   │       └── OBJECT_{o1}-{o2}.json
    │       │   └── PIXEL/
    │       │       └── {score}/
    │       │           └── PIXEL_{x1}-{x2}.json
    │       ├── object_{o}/        # 층 5: 객체
    │       │   └── node.json
    │       └── pixel_{x}/         # 층 5: 픽셀 (그리드 직속)
    │           └── node.json
    └── edges/                     # (선택) TASK 간 비교
        └── TASK_{hex1}-{hex2}.json
```

- **노드**: 각 엔티티 폴더에 **`node.json` 하나** — 해당 객체의 property dict.
- **엣지**: 해당 엔티티가 “주인”인 비교만 그 아래 `edges/`에 저장.  
  - PAIR/GRID 비교 → `pair_{p}/edges/`  
  - OBJECT/PIXEL 비교 → `grid_{g}/edges/`  
  - 타입·점수 분류는 `edges/{PAIR|GRID|OBJECT|PIXEL}/{score}/` 로만 구분.

이렇게 하면 **폴더 깊이는 “엔티티 5층”만** 쓰고, node/edge 구분은 **폴더 이름(`edges/`) + 파일 이름**으로 가능합니다.

---

## 4. 파일 이름 규칙

### 4.1 노드 (단일 객체 설명, dict 한 개)

| 위치 | 파일명 | 내용 |
|------|--------|------|
| `{task_hex}/` | `node.json` | TASK property (예: example_pair_count, test_pair_count 등) |
| `pair_{p}/` | `node.json` | PAIR property (예: grid_count, view 요약 등) |
| `grid_{g}/` | `node.json` | GRID property (height, width, colorgrid 등) |
| `object_{o}/` | `node.json` | OBJECT property |
| `pixel_{x}/` | `node.json` | PIXEL property |

- **제목**: 모두 `node.json`으로 통일해도 됨.  
  “어떤 객체에 대한 설명인지”는 **경로**로 알 수 있음:  
  `memory/007bbfb7/pair_0/grid_1/object_2/node.json` → PAIR 0, GRID 1, OBJECT 2.
- **내용**: 기존 `*_property.json`과 동일한 dict (id, type, property 필드 등).

**대안 (타입을 파일명에 넣고 싶을 때)**  
- `task.json`, `pair.json`, `grid.json`, `object.json`, `pixel.json` 처럼 타입별로 다른 이름을 쓰면, 폴더를 열었을 때 “이게 무슨 타입인지” 파일 이름만 봐도 알 수 있음.

### 4.2 엣지 (비교 결과, 두 객체 간 관계)

- **형식**: `{엔티티타입}_{id1}-{id2}.json`
- **예**:
  - `PAIR_0-1.json`
  - `GRID_0-1.json`
  - `OBJECT_0-1.json`
  - `PIXEL_0-1.json`
- **위치**:  
  - PAIR/GRID 비교 → `pair_{p}/edges/PAIR|GRID/{score}/...`  
  - OBJECT/PIXEL 비교 → `grid_{g}/edges/OBJECT|PIXEL/{score}/...`  
  score는 기존처럼 비교 결과의 `result.score`에서 추출한 숫자(0~N)로 분류.

**제목만 보면**  
- `GRID_0-1.json` → GRID 0과 GRID 1의 비교.  
- `OBJECT_2-3.json` → OBJECT 2와 3의 비교.  
- 어떤 타입의 엣지인지, 어떤 id 쌍인지 파일 이름만으로 구분 가능.

---

## 5. 분류·조회 관점에서 정리

- **“어떤 객체에 대한 설명인가?”**  
  → **경로**가 객체 식별자:  
  `memory/{task_hex}/pair_{p}/grid_{g}/object_{o}/node.json`  
  → 해당 TASK의 PAIR p, GRID g, OBJECT o의 노드.

- **“노드인가 엣지인가?”**  
  - 노드: 파일명 `node.json` (또는 `task.json` 등).  
  - 엣지: `edges/` 아래 + `{TYPE}_{id1}-{id2}.json`.

- **“어떤 타입의 엣지인가?”**  
  - `edges/PAIR/`, `edges/GRID/`, `edges/OBJECT/`, `edges/PIXEL/`  
  - 파일 이름의 접두사: `PAIR_`, `GRID_`, `OBJECT_`, `PIXEL_`.

- **“점수(유사도)별로 보고 싶다”**  
  - `edges/{TYPE}/{score}/` 아래만 보면 됨.

- **기존 id 문자열과의 대응**  
  - `007bbfb7.PAIR_nodes.0.GRID_nodes.1`  
  → `memory/007bbfb7/pair_0/grid_1/node.json`  
  - 비교 결과 경로는  
  → `memory/007bbfb7/pair_0/edges/GRID/{score}/GRID_0-1.json`  
  같은 형태로 변환 함수 하나 두면, 기존 `id_to_json_path` / `id_pair_to_comparison_path`를 새 구조에 맞게 교체할 수 있음.

---

## 6. 구현 시 변경 포인트 요약

1. **ARCKG**  
   - `task.py`, `pair.py`, `grid.py`, `object.py`, `pixel.py`, `tf_grid.py`의 `to_json()`에서  
     기존 `TASK_nodes/.../TASK_property/...` 형태 대신  
     `{task_hex}/node.json`, `pair_{p}/node.json`, `grid_{g}/node.json` 등 **5층 + node.json** 규칙으로 경로/파일명 생성.

2. **comparison.py**  
   - `id_to_json_path(id)`  
     → `memory/{task_hex}/pair_{p}/grid_{g}/.../node.json` 형태로 반환.  
   - `id_pair_to_comparison_path(id1, id2, score)`  
     → `memory/.../pair_{p}/edges/GRID/{score}/GRID_{g1}-{g2}.json` 등 **5층 + edges/** 규칙으로 반환.  
   - `json_path_to_id()`는 위 경로/파일명에서 다시 dot id 문자열 복원.

3. **파일명 선택**  
   - 노드: 전부 `node.json` vs 타입별 `task.json` 등 — 한 가지로 통일 후, 문서와 코드에 명시.

이렇게 하면 **이론적 5개 층**만 유지하면서, **제목(파일명)**과 **폴더 구조**만으로 노드/엣지와 타입을 분류·조회할 수 있습니다.
