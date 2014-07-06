""" level.py """

import random

import being
import weapon
import armor
import conf
from field import field
from item import Item
from levels import levels
from conf import log


class Level:
    """Current level map with all objects and beings."""

    __shared_state = {}

    def __init__(self):
        self.__init__ = self.__shared_state
        self.up, self.down = None, None
        self.save_monsters = []
        self.attacking_monster = None
        self.last_index = 0     # every object/being on level will have unique index

    def populate(self, kind="random"):
        """Create monsters and place them on the level map."""

        self.num = levels.current
        # make monsters
        self.monsters = []
        # keep strategic view monsters when in tactical map
        # monster we are attacking now so that we can kill him in
        # strategic view if we kill him in tactical
        num_monsters = random.randrange(2,6)
        if conf.xmax < 10: num_monsters = 1
        if conf.xmax < 2: num_monsters = 0
        monster_level = round(self.num*random.random()*6)

        for i in range(num_monsters):
            if kind == "random" or random.random() > 0.75:
                b = being.rand()
            else:
                b = kind
            log(b)
            m = being.Being(b, field.random(), self.last_index)
            self.last_index += 1
            m.place()
            m.team = 'monsters'
            log(m.loc)
            self.monsters.append(m)
            log(self.monsters)

        # make items
        #field.set(field.random(), Item('down'))
        num_items = int(round(self.num*random.random()))
        if conf.xmax < 10: num_items = 1
        if conf.xmax < 2: num_items = 0

        if num_items > 4:
            num_items = 4
        for i in range(num_items):
            if random.choice((0,1)):
                field.set(field.random(), weapon.Weapon(weapon.rand(), self.last_index))
            else:
                field.set(field.random(), armor.Armor(armor.rand(), self.last_index))
            self.last_index += 1
        if conf.mode == "tactical":
            return

        log("populate(): levels.current=%d, conf.levels: %d \n" % (levels.current, conf.levels))
        down, up = None, None
        if levels.current == 1:
            down = field.random()
            field.set(down, Item("down"))
        elif levels.current+1 == conf.levels:
            up = field.random()
            field.set(up, Item("up"))
        else:
            up = field.random()
            down = field.random()
            field.set(down, Item("down"))
            field.set(up, Item("up"))
        self.down, self.up = down, up



level = Level()
