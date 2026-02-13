# program_gen 패키지 설계

## 1. 목표

- **program.py**와 **make_rule.py**를 “프로그램 생성 관련 코드” 하나의 패키지로 묶기.
- ARCKG가 컴포넌트·비교를 패키지로 제공하는 것처럼, **규칙 기반 프로그램 생성**도 `from program_gen import ProgramManager, get_matching_actions` 형태로 쓸 수 있게 함.
- 길고 복잡한 두 파일을 역할별로 나누고, 불필요/비효율 코드를 정리.

---

## 2. 패키지 구조 제안

```
program_gen/
  __init__.py      # ProgramManager, get_matching_actions 노출
  rules.py         # 규칙 로드·조건 평가·get_matching_actions (현재 make_rule.py)
  manager.py       # ProgramManager (현재 program.py의 생성/저장/실행)
```

- **rules.py**: 비교 결과 → DSL 액션 리스트 (규칙 매칭). 순수 함수 위주.
- **manager.py**: 액션 리스트 + pair → 코드 생성·저장·실행. ProgramManager 한 클래스.
- **__init__.py**: `from program_gen.manager import ProgramManager`, `from program_gen.rules import get_matching_actions` 재노출.

---

## 3. 수정·정리 사항 (사전 설명)

### 3.1 make_rule → rules.py

| 항목 | 내용 |
|------|------|
| **미사용 import** | `from collections import deque` — 코드 내 사용처 없음 → **제거** |
| **미사용 함수** | `get_parameters(parameters)` — 정의만 있고 호출 없음 → **제거** (나중에 규칙 확장 시 필요하면 복구 가능) |
| **디버그 print** | `get_matching_actions`·`process_action_args` 안의 여러 `print()` — 동작에는 불필요. **주석 처리 또는 제거** 제안 (로그가 필요하면 나중에 logging 모듈로 대체). 여기서는 **주석 처리**로 남겨 두어, 필요 시 다시 켤 수 있게 함. |

### 3.2 program.py → manager.py

| 항목 | 내용 |
|------|------|
| **중복 코드** | `generate_program`과 `generate_program_with_rules` 안의 “action_args → kwargs 문자열” 만드는 블록이 거의 동일 (~40줄×2). **공통 헬퍼 `_action_args_to_kwargs_str(action_args)`** 로 빼서 한 곳만 유지. |
| **validate_program** | `self.task_hex_code`, `self.task`를 참조하는데, `ProgramManager.__init__`에서 설정하지 않음. 현재 그대로 두면 호출 시 AttributeError 가능. **수정**: `validate_program(self, level, task_hex_code=None, task=None)` 처럼 인자로 받거나, 호출하는 쪽이 없으면 그대로 두고 docstring에 “task_hex_code, task가 설정된 인스턴스에서만 사용” 명시. 여기서는 **인자로 받는 방식**으로 수정해, 호출부가 없어도 안전하게 호출 가능하게 함. |

### 3.3 import 변경

- **workers/arc_solver.py**: `from make_rule import get_matching_actions` → `from program_gen import get_matching_actions`, `from program import ProgramManager` → `from program_gen import ProgramManager`
- **main_program_run_manual.py**: `from program import ProgramManager` → `from program_gen import ProgramManager`
- **program_gen/manager.py**: `from make_rule import get_matching_actions` → `from program_gen.rules import get_matching_actions`

---

## 4. 사용 예 (패키징 후)

```python
from program_gen import ProgramManager, get_matching_actions
from ARCKG import compare

comparison_result = compare(input_grid, output_grid, save=False)
actions = get_matching_actions(comparison_result)

pm = ProgramManager()
program = pm.generate_program_with_rules(pair, 0, actions, base_program=...)
pm.save_program(program, 0, "GRID", task_hex_code)
```

---

이 설계대로 구현하면, 프로그램 생성 관련 코드가 한 패키지로 묶이고, 불필요 코드 제거·중복 제거·validate_program 안정화가 함께 적용됩니다.
