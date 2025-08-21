from .type import PIXELData_Type, RawData_Type


def raw_data_to_pixel_data(raw_data:RawData_Type) -> PIXELData_Type :
   return [((i,j), raw_data[i][j]) for i in range(len(raw_data)) for j in range(len(raw_data[i]))]