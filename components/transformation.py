from abc import abstractmethod


class Transformation:
    def __init__(self):
        pass

    @abstractmethod
    def execute(self):
        raise NotImplementedError