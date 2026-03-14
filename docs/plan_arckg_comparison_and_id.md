# Plan: ARCKG Comparison 및 ID 체계 통일

ARCKG 비교(comparison) 파이프라인과 ID 표기를 `docs/ARCKG_structure_spec.md` 및 논의 내용에 맞춰 통일하기 위한 구현 계획이다.

---

## 1. 목표

- **비교 결과 포맷 통일**: 0차~N차 relation 모두 동일한 `result` 구조(`type` / `score` / `category` / leaf 시 `comp1`·`comp2`) 사용.
- **단일 compare 코어**: property 비교와 relation 비교를 입력 타입에 따라 한 파이프라인에서 처리.
- **ID·파일명 통일**: 노드/엣지 ID와 json 파일 이름을 **`E_`** 로 통일 (id와 파일명이 동일 규칙).

---

## 2. 비교(comparison) 설계

### 2.1 현재 구조와 문제

- **로우 비교 트리 (A)**: `compare_nested_json` 출력 — `{"type", "comp1", "comp2", "details"}`. 내부 연산용.
- **relation result (B)**: `get_comparison_data` 출력 — `{"type", "score", "category", (leaf 시 comp1/comp2)}`. 저장·스펙용.
- **저장되는 JSON에는 `details` 없음.** `result`에는 B만 들어감.
- **문제**: 2차 이상은 입력이 이미 `type/score/category` 구조인데, 현재 compare는 “일반 dict”로만 다뤄서 `result.type`, `result.score`, `result.category` 같은 스펙 규칙을 만들지 못함.

### 2.2 통일 방향

- **relation-aware compare 코어** 하나에서:
  - 입력이 **property dict** → 기존처럼 raw diff(A) → `get_comparison_data` → 1차 relation(B).
  - 입력이 **relation result dict** (`type`/`score`/`category` 보유) → `type`, `score`, `category`를 각각 비교하고, `result.type`, `result.score`, `result.category` 등 **dot notation**으로 재귀. 결과는 동일한 B 포맷.
- 0차/1차/2차/3차 모두 이 코어 + `get_comparison_data` 로 처리. 0차는 “예외”가 아니라 property를 비교하는 동일 compare의 한 케이스.

### 2.3 구현 포인트

- **입력 타입 판별**: dict가 `type`/`score`/`category` 키를 가지면 relation result로 간주.
- **2차 이상**: `compare_relation_results(r1, r2, prefix="result")` 형태의 재귀 함수 추가. `category` 내부는 동일 함수로 재귀, 키는 `prefix.key` (예: `result.type`, `color.comp1`).
- **score**: 스펙대로 “일치 항목 수/전체 항목 수”로 계산하고, 2차 이상에서는 `type`/`score`/`category` 3개 필드를 독립적으로 비교.

---

## 3. ID 체계 (E_ 통일)

### 3.1 원칙

- **노드 ID**와 **엣지 ID**를 폴더/파일 네이밍과 맞춘다.
- **엣지 ID = 해당 json 파일 이름에서 `.json` 만 제거한 문자열** (즉 `E_` 사용, `E:` 미사용).

### 3.2 노드 ID

- 형식: `T{hex}.P{p}.G{g}.O{o}.X{x}` (필요한 계층까지만).
- 예: `T08ed6ac7.P0.G0`, `T08ed6ac7.P0.G0.X6`, `T08ed6ac7.P0.G0.O1.X3`.
- 폴더: `N_T{hex}`, `N_P{p}`, `N_G{g}`, `N_O{o}`, `N_X{x}` — 노드 ID에서 기계적으로 복원 가능.

### 3.3 엣지 ID (파일명과 동일 규칙)

| 차수 | 예시 엣지 ID (저장 시 id1/id2/edge_id·파일명에 사용) |
|------|------------------------------------------------------|
| 0차 (property) | `E_P0G0X6` (node name만으로 단일 노드 property) |
| 1차 (node vs node) | `E_P0G0X6-P0G0X7` |
| 2차 (edge vs edge) | `E_(E_P0G0X6-P0G0X7)-(E_P1G0X8-P1G0X9)` |
| 3차 이상 | `E_(E_(E_...)-(E_...))-(E_(E_...)-(E_...))` |

- **규칙**: 엣지 ID와 json 파일 이름을 **동일한 `E_...` 문자열**로 통일. `E:` 구분자 사용하지 않음.

### 3.4 comparison result JSON 필드 통일

- **0차/1차 (node vs node)**  
  - `id1`, `id2`: 노드 ID (위 노드 ID 형식).  
  - `edge_id`: 이 비교를 나타내는 엣지 ID (예: `E_P0G0X6-P0G0X7`).  
  - `order`: 0(property) 또는 1.  
  - `lca_node_id`: (선택) 저장 위치가 되는 LCA 노드 ID.  
  - `result`: `{ type, score, category, ... }`.

- **2차 이상 (edge vs edge)**  
  - `id1`, `id2`: 비교 대상 엣지 ID (예: `E_P0G0X6-P0G0X7`).  
  - `edge_id`: 이번 2차 relation 엣지 ID (예: `E_(E_P0G0X6-P0G0X7)-(E_P1G0X8-P1G0X9)`).  
  - `order`: 2, 3, …  
  - `lca_node_id`: 두 엣지의 최소 공통 조상 노드 ID.  
  - `result`: 동일 구조.

- **저장 위치**: 두 entity(노드 또는 엣지)의 **LCA node 폴더**에, 파일명 = `{edge_id}.json`.

---

## 4. LCA·경로 처리

- **노드 ID**에서 dot으로 split 후 공통 prefix로 LCA 계산.
- **엣지 ID**는 포함된 노드 ID들로부터 LCA 유도 (1차 edge면 두 노드의 LCA, 2차면 두 edge가 참조하는 노드들의 LCA 등).
- **파일 경로**: `memory/N_T{hex}/N_P{p}/.../` 아래에 `E_...json` 저장. 기존 `memory_paths` 및 `id_pair_to_comparison_path` 를 확장해 2차 이상용 `E_(E_...)-(E_...).json` 이름 생성 지원.

---

## 5. 구현 시 유의사항 (스펙 8장 반영)

- 입력이 property인지, 1차 이상 relation result인지 구분 후 동일 compare 재귀 적용.
- 2차 이상에서는 비교 항목이 항상 `type`, `score`, `category` 3개; scalar leaf에서는 `comp1`, `comp2` 추가.
- score는 category와 독립적으로 비교.
- 저장 시 이름·위치는 위 ID 규칙 및 LCA 규칙 준수.

---

## 6. 구현 TODO (요약)

1. **compare 코어 정리**: `get_comparison_data`와 스펙 예시 결과 일치 검증; relation result 입력 분기 및 `compare_relation_results` 추가.
2. **2차·3차 로직**: `type`/`score`/`category` 단위 비교 및 dot-notation `category` 키 생성.
3. **LCA·경로·네이밍**: 노드/엣지 ID 생성, `edge_id` = 파일명(확장자 제외), LCA 폴더 계산 헬퍼 통합.
4. **compare API**: 0차~N차를 하나의 진입점으로 처리, `id1`/`id2`/`edge_id`/`order`/`lca_node_id` 출력 통일.
5. **테스트**: 스펙 7장 예시 JSON으로 0차·1차·2차·3차 결과 구조·score 검증.

---

이 문서는 구현 시 변경 사항을 적용할 때 기준이 되는 계획 기록이다.
