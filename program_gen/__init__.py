"""
Program generation package: rule-based DSL action matching and program management.
"""

from program_gen.manager import ProgramManager
from program_gen.rules import get_matching_actions

__all__ = ["ProgramManager", "get_matching_actions"]
