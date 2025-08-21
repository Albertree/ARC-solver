from ARCKG.grid import GRID
from ARCKG.pair import PAIR
from components.transformation import Transformation


class TFHistory:
    def __init__(self, pair:PAIR, grid:GRID, tf_history:list[Transformation]):
        self.pair_id:PAIR = pair
        self.initial_grid:GRID = grid
        self.steps:list[Transformation] = tf_history