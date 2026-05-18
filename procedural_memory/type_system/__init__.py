"""
ARBOR 타입 시스템.

타입 정의, 이름↔값 매핑, 타입 인식 비교 분기를 제공한다.
다른 모듈(ARCKG.comparison, anti-unification 등)은 이 모듈을 호출하여
값을 type-aware하게 다룬다.

외부 인터페이스:
  - color: NAMES, name_to_value, value_to_name
  - helpers: class_eq
  - schema: NODE_SCHEMAS, get_node_schema
  - compare_dispatch: compare_typed
"""

from procedural_memory.type_system.color import (
    COLOR_NAMES,
    name_to_value,
    value_to_name,
)
from procedural_memory.type_system.classes import get_class_cardinality
from procedural_memory.type_system.helpers import class_eq
from procedural_memory.type_system.schema import NODE_SCHEMAS, get_node_schema
from procedural_memory.type_system.compare_dispatch import compare_typed

__all__ = [
    "COLOR_NAMES",
    "name_to_value",
    "value_to_name",
    "get_class_cardinality",
    "class_eq",
    "NODE_SCHEMAS",
    "get_node_schema",
    "compare_typed",
]
