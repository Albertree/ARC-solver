

# def is_empty_program(program):
#     return len(program) == 0


# def get_component_full_id(component):
#     if component.type == "task":
#         return (component.hex_code, None, None, None, None, component.type)
#     elif component.type == "pair":
#         return (component.parent.hex_code, component.id, None, None, None, component.type)
#     elif component.type == "grid":
#         return (component.parent[0].parent.hex_code, component.parent[0].id, component.id, None, None, component.type)
#     elif component.type == "object":
#         return (component.parent[0].parent[0].parent.hex_code, component.parent[0].parent[0].id, component.parent[0].id, component.id, None, component.type)
#     elif component.type == "pixel":
#         return (component.parent[0].parent[0].parent.hex_code,component.parent[0].parent[0].id, component.parent[0].id, None, component.id, component.type)
#     elif component.type == "tfgrid":
#         return (component.parent[0].parent.hex_code, component.parent[0].id, component.id, None, None, component.type)
#     else:
#         raise ValueError("Invalid component type")