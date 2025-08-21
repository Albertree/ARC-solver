from components.abstraction_rule import AbstractionRule
from components.condition import Condition
from components.rule import Rule
from components.transformation_history import TFHistory
from managers.cli_manager import CLIManager
from managers.task_manager import TASKManager
from ARCKG.pair import PAIR
from ARCKG.object import OBJECT
from ARCKG.pixel import PIXEL
from workers.tf_abstractor import TFAbstractor
from workers.tf_generator import TFGenerator


class Solver() :
    def __init__(self,task: TASKManager) :
        self.cli:CLIManager = CLIManager()
        self.task_pairs:list[PAIR] = task.get_example_pairs()
        self.tf_storage:list[TFHistory|None] = [None]*len(self.task_pairs)
        

    def run(self) :
        generator = TFGenerator(self.task_pairs)
        abstractor = TFAbstractor()

        group_pixel_rule = AbstractionRule(from_type=list[PIXEL], to_type=OBJECT,condition=Condition(OBJECT.contains))

        tf_history = generator.generate_tfhistory(self.task_pairs[0])
        self.cli.visualize_tf_history(tf_history)
        tf_history = abstractor.generalize(tf_history,rule=group_pixel_rule) # tf 1 to 2
        tf_history = abstractor.generalize(tf_history,rule=group_pixel_rule) # tf 2 to 3


        pass

# printcg