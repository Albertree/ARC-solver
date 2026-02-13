# Working Memory 구성 및 정보 호출/저장 (병목 방지)

## 1. Working Memory 구성

Working Memory(작업 기억)는 **디스크에 저장하지 않고**, 한 번의 풀이 세션 동안만 RAM에 유지되는 “현재 풀이 상태”입니다.

### 1.1 담을 정보 (구조)

| 구성 요소 | 내용 | 소스 |
|----------|------|------|
| **현재 태스크** | `task_hex`, 로드된 TASK 객체(또는 참조) | ARCManager + (선택) Semantic |
| **현재 PAIR/입출력** | 풀이 중인 pair_idx, input_grid, output_grid | TASK.example_pairs[pair_idx] |
| **현재 목표** | “GRID 레벨 풀이 중” / “OBJECT 레벨 풀이 중” 등 | 솔버 상태 |
| **선택된 규칙/후보** | `get_matching_actions` 결과, 적용할 rules 리스트 | Procedural 조회 + comparison |
| **중간 결과** | `grid_result`, `TF_GRID` 체인, 부분 프로그램 | ProgramManager 실행 결과 |
| **이번 에피소드용 버퍼** | 기록할 steps, reasons, 생성된 프로그램 | 풀이 중 누적 → 에피소드 기록 시 사용 |

즉, **구성** = 위 항목들을 필드로 갖는 in-memory 구조(클래스/딕셔너리) 하나로 두고, 솔버와 ProgramManager가 이 구조를 읽고 씁니다.

### 1.2 코드에서의 위치

- **물리적 저장**: 없음 (파일/DB 미사용).
- **코드 배치**: `memory_system/working.py`에서 `WorkingMemory` 클래스(또는 네임드 튜플/데이터클래스)로 정의하고, `ARCSolver`가 인스턴스 하나를 풀이 시작 시 생성·풀이 종료까지 유지.

예시 (요지):

```python
# memory_system/working.py
class WorkingMemory:
    def __init__(self):
        self.task_hex: str | None = None
        self.task: TASK | None = None
        self.pair_idx: int | None = None
        self.current_goal: str = ""           # "GRID" | "OBJECT" | ...
        self.candidate_rules: list = []
        self.partial_program: list = []
        self.steps: list = []                 # 에피소드 기록용
        self.reasons: list = []               # 에피소드 기록용
        self.grid_result: GRID | None = None
```

---

## 2. 정보의 호출(조회) 및 저장(갱신)

### 2.1 호출(Working Memory로 들어오는 정보)

- **풀이 시작 시 (한 번)**  
  - Semantic: 필요 시 “이미 본 문제 구조” 로드 → WM의 현재 태스크/PAIR 보강.  
  - Episodic: `retrieve_by_task(task_hex)` 등으로 과거 시도 조회 → WM의 `candidate_rules`/전략 참고용으로만 사용 (선택).  
  - Procedural: `get_candidate_programs(problem_signature)`로 후보 프로그램/규칙 조회 → WM의 `candidate_rules` 또는 초기 전략에 반영.  
  - 이때 **디스크/DB 읽기는 풀이 시작 시 한 번만** 수행하고, 그 결과를 WM 필드에 넣습니다.

- **풀이 루프 안**  
  - 모든 “무엇을 적용할지 / 현재 그리드 / 중간 결과”는 **Working Memory와 솔버/ProgramManager 변수만** 참조.  
  - 루프 내부에서는 Semantic/Episodic/Procedural에 대한 **추가 디스크 읽기 없음**.

### 2.2 저장(Working Memory에서 나가는 정보)

- **Working Memory 자체는 디스크에 저장하지 않습니다.**  
  “저장”은 “WM 내용 중 일부를 Long-Term Memory로 옮기는 것”으로만 이뤄집니다.

- **풀이 종료 시 (한 번)**  
  - WM(및 솔버)에 쌓아둔 `steps`, `reasons`, 생성된 프로그램, 성공/실패를 모아서:  
    - **Episodic**: `record(episode)` 호출 → `memory/episodic/`에 파일로 기록.  
    - **Procedural**: 성공 시 `store_program(...)` 호출 → `memory/procedural/`에 파일로 기록.  
  - 즉, **디스크 쓰기는 에피소드/절차 저장 시에만** 발생합니다.

정리하면:

- **호출**: LTM → WM 은 “풀이 시작 시” 한 번 로드.  
- **저장**: WM → LTM 은 “풀이 종료 시” 한 번 기록.  
- **풀이 중**: WM은 메모리에서만 읽고 갱신하며, 디스크 I/O 없음.

---

## 3. 물리적 파일 저장으로 인한 병목 완화

- **Working Memory**: 파일 저장 없음 → 저장 병목 자체가 없음.
- **Semantic (ARCKG)**:  
  - 읽기: 풀이 시작 시 필요한 태스크/PAIR만 로드하거나, 이미 ARCManager로 로드한 객체를 WM에 넣기만 하면 됨.  
  - 쓰기: ARCKG `to_json()` 호출 시점을 “풀이 종료 시 한 번” 또는 “태스크 로드 후 구조 저장 시 한 번”으로 제한하면, 풀이 루프 안에서는 쓰기 없음.
- **Episodic / Procedural**:  
  - 읽기: 풀이 시작 시 한 번만 (위와 동일).  
  - 쓰기: 에피소드/프로그램 저장을 **풀이 종료 시 한 번**으로 묶고, 필요하면 아래처럼 완화 가능.  
    - **비동기 쓰기**: `record()`, `store_program()`을 별도 스레드/비동기 태스크로 실행해, 솔버는 바로 다음 태스크로 진행.  
    - **쓰기 버퍼**: 에피소드/프로그램을 메모리 큐에 넣고, 백그라운드에서 순차적으로 디스크에 flush.  
    - **배치 쓰기**: 여러 에피소드를 모아 두었다가 한 번에 파일로 쓰기 (인덱스는 마지막에 갱신).

이렇게 하면 “저장이 물리적인 파일로 저장되는 것”이 풀이 루프 안에서 병목이 되지 않고, Working Memory는 항상 메모리만 사용하므로 호출/저장 흐름이 단순하고 빠르게 유지됩니다.
