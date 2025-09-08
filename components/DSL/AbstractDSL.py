from DSL.enums import DSLType, DSLName
from DSL.ParamType import ParamType


class AbstractDSL:
    name = DSLName.UNKNOWN
    dsl_type = DSLType.UNKNOWN
    args_keys = []
    args_types = []
    apply_function = None
    args = []

    def get_apply_function(self):
        return self.apply_function
    
    def get_args_list(self):
        return self.args

    def get_args_keys(self):
        return self.args_keys

    def get_args_types(self):
        return self.args_types
    
    def get_args_json(self):
        result = {}
        for i in range(len(self.args_keys)):
            result[self.args_keys[i]] = self.args[i]
        return result

    def read_input_args(self):
        params = input("> ")
        params = params.split(" ")
        self.args = []
        for i in range(len(params)):
            self.args.append(ParamType.cast(params[i], self.args_types[i]))
        
        return
    
    def set_args(self, args):
        self.args = args

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        return self.name == other.name
    
    def __hash__(self):
        return hash(self.name)

