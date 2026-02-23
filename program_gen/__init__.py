"""
Program generation package: rule-based DSL action matching, program management,
and abstraction of pair-specific programs via anti-unification.
"""

from program_gen.manager import ProgramManager
from program_gen.rules import get_matching_actions
from program_gen.anti_unification import (
    anti_unify_programs,
    abstract_task_programs,
    load_pair_programs,
    save_abstract_program,
    program_lines_to_terms,
    terms_to_program_lines,
)

__all__ = [
    "ProgramManager",
    "get_matching_actions",
    "anti_unify_programs",
    "abstract_task_programs",
    "load_pair_programs",
    "save_abstract_program",
    "program_lines_to_terms",
    "terms_to_program_lines",
]
