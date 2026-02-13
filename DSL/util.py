

def add_added_color(**kwargs):
    colorlist = kwargs.get('colorlist')
    color = kwargs.get('color')
    if color not in colorlist:
        colorlist.append(color)

def add_removed_color(**kwargs):
    colorlist = kwargs.get('colorlist')
    color = kwargs.get('color')
    if color not in colorlist:
        colorlist.append(color)




