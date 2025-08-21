from components.condition import Condition
from components.transformation import Transformation
from components.transformation_history import TFHistory


class Rule: # todo : change to transformation rule 
    def __init__(self,conditions:list[Condition], transformation: list[Transformation]):
        self.conditions:list[Condition] = conditions
        self.actions:list[Transformation] = transformation

    def is_applicable(self, to:TFHistory) ->bool:
        # Check if all conditions are satisfied for this transformation history
        # For now, return True as a placeholder - implement condition checking logic
        return True

