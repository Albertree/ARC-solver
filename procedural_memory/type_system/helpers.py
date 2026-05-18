"""
class 타입 값을 다룰 때 쓰는 헬퍼.

규칙: class<X> 값을 직접 ==, !=, +, - 등으로 비교/연산하지 말 것.
이 헬퍼들로 의도를 명시한다.
"""


def class_eq(a, b) -> bool:
    """두 class 값이 같은지 판정. 타입이 다르면 False."""
    if type(a) is not type(b):
        return False
    return a == b
