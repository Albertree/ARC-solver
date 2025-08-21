from abc import abstractmethod


class ARCKGComponent():
    def __init__(self,id:int, type:str):
        self.id = id
        self.type = type

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def from_json(data_dict) :
        pass