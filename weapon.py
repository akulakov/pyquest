'''

weapon.py

 def rand():
    """Return random weapon.

    Higher class of weapon is usually returned when current level is high.
    """

 class Weapon:
    """Weapon class."""
     def __init__(self, kind):

     def __str__(self):


'''

import curses
import random

weapons = {
    'stiletto'              :   1,
    'vibro stiletto'        :   5,
    'shortsword'            :   2,
    'sharpcutter shortsword':   6,
    'longsword'             :   3,
    'razor longsword'       :   7,
    'katana'                :   4,
    'feather katana'        :   8,
    'death claw blade'      :   11,
    'frost brand'           :   17,
}


def rand():
    """Return random weapon.

    Higher class of weapon is usually returned when current level is high.
    """
    from level import level
    while True:
        weapon = random.choice(list(weapons.keys()))
        attack = weapons[weapon]
        roll = random.randrange(1, 18)
        roll2 = random.randrange(1, level.num*5)
        if roll >= attack and roll2 >= attack:
            return weapon


class Weapon:
    """Weapon class."""
    def __init__(self, w_type, index):
        self.index       = index
        self.char        = ')'
        self.kind        = "weapon"
        self.attack      = weapons[w_type]
        self.description = w_type
        self.alive       = 0
        self.block       = 0
        self.color       = 1

    def __str__(self):
        return self.char
