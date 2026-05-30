"""
DSL — ARBOR 그리드 풀이 DSL (Slice 1).

두 얼굴:
  · 실행 본체 (procedural) = 이 패키지의 함수들
  · 선언적 명세 (semantic 라이브러리 씨앗) = registry.SPECS

종류:
  · transformation — coloring, make_grid (동결 원자 2개)
  · property       — pair_count, grid_count, size, color, contents (to_json 노출)
  · util           — pairs_of, grids_of, role_of, filter_, elements_at
  · relation (C)   — select, compare, compare_set  (Inter-* 비교; Intra=descent 는 모듈 A)
"""

from procedural_memory.DSL.registry import SPECS, spec, body

# 서브모듈 import = @dsl 데코레이터 실행 → SPECS 등록
import procedural_memory.DSL.util            # noqa: F401,E402
import procedural_memory.DSL.property        # noqa: F401,E402
import procedural_memory.DSL.transformation  # noqa: F401,E402
import procedural_memory.DSL.relation        # noqa: F401,E402

__all__ = ["SPECS", "spec", "body"]
