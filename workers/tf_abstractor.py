from ARCKG.pair import PAIR
from components.rule import Rule
from components.transformation_history import TFHistory


class TFAbstractor :
    def __init__(self):
        self.abst_rules:list[Rule] = []
        pass

    def is_abstract(self,tf_history:TFHistory,tf_histories:list[TFHistory]):
        for rule in self.abst_rules :
            if rule.is_applicable(to=tf_history):
                return False
        
        return True

    def compress(self,tf_history:TFHistory):
        # todo: implement
        return tf_history

    def generalize(self,tf_history:TFHistory,rule:Rule) -> TFHistory:
        # todo : implement
        return tf_history
    
    # todo : overload function generalize : to result list of TFHistory candidates

    def abduction(self,tf_histories:list[TFHistory]) -> Rule:
        # in brainstorming.
        # With the tf histories, wouldn't it be possible to derive a probable rule?
        raise NotImplementedError
        return Rule()
