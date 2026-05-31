"""
program — 지식 추상화 패키지.

Public interface:
    anti_unify_objects  — example 산물을 일반화해 schema 추출 (const / from_g0)
    is_solvable         — schema 가 전부 설명되는가
"""

from program.anti_unification import anti_unify_objects, is_solvable

__all__ = ["anti_unify_objects", "is_solvable"]
