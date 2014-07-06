'''armor.py



armor.py

armor - dictionary of armour types. name: rating

 def rand():
    """Return random armor type.

    If current level is high, armor tends to be better.
    """

 class Armor:

     def __str__(self):
        """Return char representation for our armor type."""
'''

import curses
import random


armor = {
    'leather'                    : 1,
    'chain mail'                 : 2,
    'plate'                      : 3,
    'mithril'                    : 4,
    'crystal'                    : 5,

    'titanium studded leather'   : 6,
    'fused chain mail'           : 7,
    'titanium reinforced plate'  : 8,
    'gold dwarven mithril'       : 9,
    'diamond crystal'            : 10,

    'nanotube reinforced kevlar' : 14,
    'red dragon scale'           : 17,
    'black dragon scale'         : 25,
}


def rand():
    """Return random armor type.

    If current level is high, armor tends to be better.
    """
    from level import level
    while True:
        arm = random.choice(list(armor.keys()))
        dfn = armor[arm]
        roll = random.randrange(1, 18)
        roll2 = random.randrange(1, level.num*5)
        if roll >= dfn and roll2 >= dfn:
            return arm


class Armor:
    def __init__(self, _type, index):
        """Init armor instance."""
        self.index       = index
        self.char        = '&'
        self.defense     = armor[_type]
        self.kind        = "armor"
        self.description = _type
        self.alive       = 0
        self.block       = 0
        self.color       = 1


    def __str__(self):
        """Return char representation for our armor type."""
        return self.char
