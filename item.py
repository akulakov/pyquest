'''
item.py

 class Item:
    """An inanimate thing."""
     def __init__(self, kind):

     def __str__(self):
        """Return char representation of our thing."""

'''

import curses

items = {
    'wall'      : ('#',1, ("stationary",)),
    'corpse'    : ('%',0, ()),
    'empty'     : (' ',0, ("stationary",)),
    'down'      : ('>',0, ("stationary",)),
    'up'        : ('<',0, ("stationary",)),
    'vertice'   : ('V',0, ("stationary", "invisible")),
    'mark'      : ('~',0, ("stationary",)),
}


class Item:
    """An inanimate object."""
    # __slots__ = "index char block specials kind alive description color".split()

    def __init__(self, kind, index=None):
        self.index = index
        (self.char,
         self.block,
         self.specials) = items[kind]

        self.kind        = kind
        self.alive       = False
        self.description = 'item'
        self.color       = 1

    def __str__(self):
        """Return char representation of our thing."""
        # this does not work now because we save items in maps.. maps should
        # be fixed to be saved without instances.. just with descriptions.. csv?
        # if "invisible" in self.specials:
        #     return None
        # else:
        return self.char
