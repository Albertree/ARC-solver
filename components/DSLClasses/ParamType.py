from enum import Enum

class ParamType(Enum):
    INT = "int"
    COORD_TUPLE = "coord_tuple"
    LIST_OF_COORD_TUPLES = "list_of_coord_tuples"
    COLOR = "color"
    ROTATE_DIRECTION = "rotate_direction"
    LINE_FLIP_DIRECTION = "line_flip_direction"
    EIGHT_DIRECTION = "eight_direction"

    @staticmethod
    def cast(value, type_enum):
        match type_enum:
            case ParamType.INT:
                return int(value)
            case ParamType.COORD_TUPLE:
                return str_to_coord_tuple(value)
            case ParamType.LIST_OF_COORD_TUPLES:
                return str_to_list_of_coord_tuples(value)
            case ParamType.COLOR:
                return int(value)
            case ParamType.ROTATE_DIRECTION:
                if value in ["cw", "ccw"]:
                    return value
                else:
                    raise ValueError(f"Invalid rotate direction: {value}")
                
            case ParamType.LINE_FLIP_DIRECTION:
                if value in ["hori", "verti", "diag", "anti"]:
                    return value
                else:
                    raise ValueError(f"Invalid line flip direction: {value}")

            case ParamType.EIGHT_DIRECTION:
                if str_to_coord_tuple(value) in [(1,0), (0,1), (-1,0), (0,-1), (1,1), (-1,-1), (-1,1), (1,-1)]:
                    return str_to_coord_tuple(value)
                else:
                    raise ValueError(f"Invalid eight direction: {value}")
            case _:
                raise ValueError(f"Invalid parameter type: {type_enum.value}")
                    
                        

# parses string of format [(INT,INT),(INT,INT),(INT,INT)..] to list of tuples
def str_to_list_of_coord_tuples(string):
   
    string = string.strip('[]').replace(" ", "").replace("),(", "), (")
    tuple_strs = string.split(', ')

    return [str_to_coord_tuple(coord) for coord in tuple_strs]


# parses string of format (INT,INT) to tuple
def str_to_coord_tuple(string):
    return tuple(map(int, string.strip('()').replace(" ", "").split(',')))


