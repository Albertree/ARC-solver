"""
class<X> 타입의 cardinality 조회.

set<class<X>> 비교 시 universe(분모)로 사용된다.
새 class 타입(direction, axis 등)이 추가되면 여기에 등록한다.
"""

from procedural_memory.type_system.color import COLOR_NAMES


_CLASS_NAMES = {
    "color": COLOR_NAMES,
    # 예시: "direction": ["UP", "DOWN", "LEFT", "RIGHT"],
}


def get_class_cardinality(class_name: str):
    """class<X>의 X 이름으로 cardinality(원소 수) 조회.
       등록되지 않은 class면 None 반환 — 호출자가 fallback 처리."""
    names = _CLASS_NAMES.get(class_name)
    return len(names) if names is not None else None
