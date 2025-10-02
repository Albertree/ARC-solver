from typing import Any
from ARCKG.grid import GRID
from .dsl_abstract import AbstractDSL
from .dsl_transformation import *
from .dsl_information import *
from enum import Enum

# {
#     "id" : "07fed1ed.pair_0.<program_count>",
#     "1" : {

#     },
#     "2" : {

#     },
#     ...
#     "n" : {

#     }
# }

class Program() :
    id = 0
    
    def __init__(self, id) -> None:
        self.id = id # should use new_id function for program maintainance.
        self.index = 0
        self.program_variables = ProgramVarStorage('value')
        self.program_grids = ProgramVarStorage('grid')
        self.nodes: list[ProgramNode]  = None

    ### Program property manipulation methods ### 

    def set_id(self,id:str) -> None :
        self.id= id
    
    def set_nodes(self,node_list) :
        self.initial_nodes = node_list

    def append_initial_node(self,node,prior_node_id) :
        # self.tree.append(program_node)
        pass


    @classmethod
    def splice(self,new_id:str,start_idx:int, end_idx:int):
        spliced = Program(new_id)
        spliced.set_tree(self.subprograms[start_idx:end_idx])
        self.set_tree(self.subprograms[:start_idx]+self.set_subprograms[end_idx:])
        return spliced

    #### class parsing methods ####

    def to_dict(self) -> dict:
        dict_output = {"id" : str(self.id)}
        dict_output.update(self.subprograms_to_dict())
        return dict_output       

    def subprograms_to_dict(self) -> dict:
        dict_output = {}
        for idx, program in enumerate(self.subprograms) :
            if isinstance(program, Program) :
                dict_output[str(idx)] = program.subprograms_to_dict()
            elif isinstance(program,AbstractDSL) : 
                dict_output[str(idx)] = program.to_dict()
        
        return dict_output
    
    def to_raw_python_string(self) -> None:
        python_string = ""

        return python_string
    
    def to_python_string(self) -> None:
        python_string = ""
        for idx, program in enumerate(self.subprograms) :
            if isinstance(program, Program) :
                python_string += program.to_raw_python_string()
            elif isinstance(program,AbstractDSL) : 
                python_string += program.to_raw_python_string()
        
        return python_string

    ### Program application methods ### 

    def execute(self,grid:GRID) -> GRID :
        for init_node in self.tree.get_init_nodes() :        
            return
        pass

    
    ### double underscore methods ### 

    def __len__(self) -> int :
        return len(self.subprograms.keys())-1

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.subprograms):
            item = self.subprograms[self.index]
            self.index += 1
            return item
        else:
            raise StopIteration


    ### Static methods ###

    @staticmethod
    def new_id():
        Program.id +=1
        return Program.id

    @staticmethod
    def merge(target1,target2) :
        # Exception fallback
        if not (isinstance(target1,Program) and isinstance(target2,Program)) :
            raise ValueError

        else :
            new_program = Program(Program.new_id())
            new_program.set_subprograms(target1.subprograms+target2.subprograms)
            return new_program

    @staticmethod
    def compare(target1,target2) : 
        # Exception fallback
        if not (isinstance(target1,Program) and isinstance(target2,Program)) :
            raise ValueError
        
        else :
            pass


class ProgramStatus(Enum) :
    INIT_NODE="init_node"
    NOT_READY = "not_ready"
    READY = "ready"
    IN_PROGRESS="in_progress"
    DONE="done"

# programNode metadata example
# {
#     'vars' : ['grid','ccw'],
#        
# }


# programNode result parcel example
# {
#     '3' : {                 # variables for node id 3
#         'grid' : ('tfg',3),    # node id 3's 'grid' variable can be accessed via tfg3
#     },
#     '4' : {
#         'ccw' : ('x',2)        # node id 4's 'ccw' variable can be accessed via x2
#     }   
# }


class ProgramNode():
    def __init__(self, node_id, next_nodes:list[int], 
                 dsl:AbstractDSL,                
                 ) :
        self.id = node_id
        self.next_nodes = next_nodes
        self.dsl = dsl
        self.dsl

        self.vars = {}
        for key in dsl.args.keys():     # dsl args are 
            self.vars[key] = None       # initialize all vars into None

    def save_prior_results(self,parcels) :
        if str(self.id) in parcels.keys() :
            my_parcel = parcels[str(self.id)]
            for key in my_parcel.keys():
                symbol, idx = my_parcel[key]
                self.vars[key] = ProgramVarStorage.get_var(symbol,idx)
        

    def run_dsl(self):
        self.dsl.core_function(**(self.vars))
        return {}
    
    def is_ready(self):
        for key in self.vars.keys() :
            if self.vars[key]==None :
                return False
        
        return True

    def execute(self):
        if len(self.prior_nodes) >0 : 
            for prior_node in self.prior_nodes :
                if not prior_node.is_ready() :
                    prior_node.execute()
    
        result = self.dsl.run_dsl()
        for nodes in self.next_nodes :
            nodes.save_prior_results(result)
        
        return True

            


class ProgramVarStorage():
    registered_symbols = [] # symbols that are already in use with other ProgramVarManager instances ex) x, y, z, ...
    vars = {}

    def __init__(self) :
        pass
    
    def append_symbol(symbol:str) :
        if symbol in ProgramVarStorage.registered_symbols :
            raise ValueError
        else : 
            ProgramVarStorage.registered_symbols.append(symbol)
            ProgramVarStorage.vars[symbol] = []

    @staticmethod
    def append_var(symbol:str,value) -> tuple[str,int]:
        if not(symbol in ProgramVarStorage.registered_symbols) :
            raise ValueError("unknown variable symbol")

        else :
            ProgramVarStorage.vars[symbol].append(value)
            idx = len(ProgramVarStorage.vars[symbol])-1
            return (symbol,idx)
     
    @staticmethod
    def save_var(symbol:str,idx:int, value) -> None:
        if not((symbol in ProgramVarStorage.registered_symbols) and idx< len(ProgramVarStorage.vars[symbol])):
            raise ValueError
        
        else :
            ProgramVarStorage.vars[symbol][idx] = value
    
    @staticmethod
    def get_var(symbol:str,idx:int) :
        if not((symbol in ProgramVarStorage.registered_symbols) and idx< len(ProgramVarStorage.vars[symbol])):
            raise ValueError
        
        else :
            return ProgramVarStorage.vars[symbol][idx]
    
    @staticmethod
    def update(updates:dict[str,Any]) :
        for key in updates.keys():
            ProgramVarStorage.save_var(key,updates[key])


