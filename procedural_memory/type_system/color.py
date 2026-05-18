"""
class<color> 정의 및 NAME ↔ INT 매핑.

내부 코드는 INT로 통일해 다루지만, 단일 슬롯(PIXEL.color 등)을
JSON으로 직렬화할 때는 NAME 문자열로 기록한다.
"""

COLOR_NAMES = [
    "ZERO", "ONE", "TWO", "THREE", "FOUR",
    "FIVE", "SIX", "SEVEN", "EIGHT", "NINE",
]

_NAME_TO_VALUE = {name: i for i, name in enumerate(COLOR_NAMES)}
_VALUE_TO_NAME = {i: name for i, name in enumerate(COLOR_NAMES)}


def name_to_value(name: str) -> int:
    """NAME 문자열을 0~9 INT 값으로 변환."""
    if name not in _NAME_TO_VALUE:
        raise ValueError(f"Unknown color name: {name!r}")
    return _NAME_TO_VALUE[name]


def value_to_name(value: int) -> str:
    """0~9 INT 값을 NAME 문자열로 변환."""
    if value not in _VALUE_TO_NAME:
        raise ValueError(f"Color value out of range (0-9): {value!r}")
    return _VALUE_TO_NAME[value]
