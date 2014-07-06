"""Being.py"""

# Imports {{{
import random
import curses
import time
from operator import itemgetter
from pprint import PrettyPrinter
from level import level
from levels import levels
from field import field
from item import Item
import conf
from conf import log
from board import Loc

from utils import *
# }}}

# vars {{{
mod = 5     # add to all monsters' stats

m = mod
beings = {
    # name : (char, health, attack, defense, color)
    'bug'                   : ('x',4+m,4+m,4+m, 3, ("animal",)),
    'gnome'                 : ('g',5+m,5+m,5+m, 3, ("magical",)),
    'elf'                   : ('e',6+m,6+m,6+m, 3, ("magical",)),
    'tiger'                 : ('t',7+m,7+m,7+m, 4, ("animal",)),
    'snake'                 : ('s',8+m,8+m,8+m, 5, ("animal",)),
    'troll'                 : ('t',9+m,9+m,9+m, 6, ("magical",)),

    'atom bug'              : ('X',10+m,10+m,10+m,3, ("animal",)),
    'elder gnome'           : ('G',11+m,11+m,11+m,3, ("magical",)),
    'noble elf'             : ('E',12+m,12+m,12+m,3, ("magical",)),
    'sabre tooth'           : ('T',13+m,13+m,13+m,4, ("animal",)),
    'royal cobra'           : ('S',14+m,14+m,14+m,5, ("animal",)),
    'dark oath troll'       : ('T',15+m,15+m,15+m,6, ("magical",)),

    'yaga'                  : ('Y',31+m,18+m,11+m, 6, ("magical",)),
    'kaschey the immortal'  : ('K',35+m,24+m,11+m, 6, ("magical",)),

    'party'                 : ('@',35,20,12, 7, ()),
    'dog'                   : ('d',10,10,5,7, ("animal",)),

    'hoplite'               : ('H',43,13,18, 7, ()),
    'fencer'                : ('F',33,18,10, 7, ()),
    'mage'                  : ('M',25,15,6, 7, ()),
}

# don't auto-create these beings
special = "dog hoplite fencer mage party".split()
# }}}


def rand():
    """ Return random monster name.
        If level.num is high, stronger monsters are more likely to be returned.
    """
    while True:
        being = random.choice( list(beings.keys()) )

        # hero's team
        if being in special:
            continue
        health = beings[being][1]
        if health > random.randrange(40):
            continue
        if health > random.randrange(level.num*10):
            continue
        return being


class Being:
    """A living being."""
    level_points = {2:200, 3:500, 4:1000, 5:2000, 6:4000, 7:8000, 8:16000, 9:32000, 10:64000}

    def __init__(self, kind, location, index):
        """ Kind can be 'hero' or 'bug', for example.
            Location is a pair x,y.
        """

        self.experience           = 0
        self.refresh_path_counter = 0        # refresh path when 0
        self.path_list            = None     # list of programmed moves
        self.loc                  = location
        self.description          = 'being'
        self.block                = True     # can't move over us
        self.program              = None     # autopilot program
        self.weapon               = None
        self.armor                = None
        self.alive                = True
        self.auto_move            = False
        self.attack_hero_flag     = False    # use autopilot to attack the hero
        self.team                 = None     # if someone else is on this team, don't attack
        self.hostile              = True
        self.asked                = False    # asked hero a question, don't ask again
        self.index                = index
        self.inventory            = []
        self.level                = 1
        self.set_kind(kind)                  # set attack, defense var, etc

    def __repr__(self):
        """Return our ascii character."""
        return self.char

    def place(self, loc=None):
        """Place me somewhere on the map.."""
        self.loc = loc or self.loc
        if self.loc:
            field.set(self.loc, self)

    def down(self):
        """ Go down the stairs

            * save old level, check if lower level exists, load it if it does,
            * otherwise create it, change current level num
        """
        if not field.contains(self.loc, "down"):
            field.text.append("Need a staircase to descend.")
            return
        cur = levels.current
        levels.list[cur] = field.fld
        cur += 1
        levels.current = cur
        if levels.list[cur]:
            field.fld, down, up = levels.list[cur]
        else:
            field.blank()
            for ltype, lnumbers in conf.level_types.items():
                if cur in lnumbers:
                    field.load_map( ltype.replace('_', ' ') )
                    break
            level.populate()
        self.place(level.up)
        field.full_display()


    def up(self):
        """Go up the stairs."""
        if not field.contains(self.loc, "up"):
            field.text.append("Need a staircase to ascend.")
            return
        cur = levels.current
        levels.list[cur] = field.fld, level.down, level.up
        cur -= 1
        field.fld, level.down, level.up = levels.list[cur]
        field.full_display()

    def ask(self, being):
        """Monster asks player some kind of question about science, etc."""
        import ask_rquestion
        if not ask_rquestion.questions:
            ask_rquestion.load_questions()
        q              = random.choice(ask_rquestion.questions)[1]
        question       = ask_rquestion.ask_text(q)
        question       = list(question)
        # question[0]    = self.kind + ": " + question[0]
        field.question = question
        rval           = field.ask()

        if rval:
            # nothing for now, later give money or a random artifact
            field.text.append(("%s is content with the answer." % self.kind, 3))
            self.hostile = False
            # self.remove()
        else:
            h = being.health
            hit = random.randint(1,6)
            if h - hit < 2:
                hit = h - 2
            being.health -= hit
            tpl = "%s's curiosity unsatisfied, he slaps hero with a textbook for %s HP"
            field.text.append( (tpl % (self.kind, hit), 5) )
        self.asked = True

    def find_closest_monster(self):
        """ Used by hero's team. UNUSED

            Bug: finds closest by straight line even if it's blocked. Returns
            the monster instance.
        """
        from level import level
        lst = []
        for being in level.monsters:
            log(repr(self.loc))
            log(being, repr(being.loc))
            if being.alive:
                lst.append( (field.distance(self.loc, being.loc), being) )
        lst.sort(key=itemgetter(0))
        if lst:
            return lst[0][1]

    def set_kind(self, kind):
        """Assign various instance vars."""
        self.char, self.health, self.attack_val, self.defense_val, self.color, self.specials = beings[kind]
        self.max_health = self.health
        self.kind = kind

    def heal(self):
        """Heal thyself, if lucky."""
        if random.random() > 0.25:
            if self.health < self.max_health:
                self.health += 1

    def random_move(self):
        dir = random.choice(conf.directions)
        self.move(dir)

    def attack_closest_monster(self):
        """Attack closest monster automatically."""
        self.auto_move = True
        dist = field.distance
        distances = [ (dist(self, m), m) for m in level.monsters if m.hostile ]
        if not distances:
            return
        monster = sorted(distances, key=itemgetter(0))
        monster = monster[0][1]
        path = self.fullpath(monster)
        if not path:
            self.auto_move = False
            return
        if len(path) == 1:
            self.attack(monster)
            self.auto_move = False
        else:
            self.move_to(path[0])

    def attack_hero(self, target=None):
        """Attack hero by autopilot."""
        if self.hostile:
            target = target or level.hero
            self.attack_hero_flag = True
            log(10)
            path = self.fullpath(target.loc)
            log(20)
            loc = first(path)
            if loc:
                self.move_to(Loc(*loc))

    def move(self, direction):
        """ Move in direction.
            Direction is a curses number corresponding to the direction key (hjkl etc).
        """
        loc = field.get_coords(self.loc, direction)
        return self.move_to(loc)

    def move_to(self, loc):
        """ Move to location.
            Location is an (x, y) tuple.
        """

        move_result = None
        if loc != self.loc:
            move_result = field.set(loc, self)
            if move_result == 3:
                self.program = None
            if move_result in (1, 4):
                # redraw cell where we just were
                field.pop(self.loc)
                field.redraw(self.loc)

                # paint us on a new cell
                self.loc = loc
                field.scr.move(loc.y-1, loc.x-1)    # ??
                field.redraw(loc)

                # pick up items
                items = field[loc]
                being = level.hoplite if self.kind=="party" else self

                for item in items:

                    # pick up armor
                    if item.kind == 'armor':
                        if not self.armor or self.armor.defense >= item.defense:
                            being.inventory.append(self.armor)
                            being.armor = item
                            field.remove(loc, item)
                            field.text.append('%s picked up %s armor' % (being.kind, item.description))
                        self.program = None

                    # pick up weapons
                    elif item.kind == 'weapon':
                        if not self.weapon or self.weapon.attack >= item.attack:
                            being.inventory.append(self.weapon)
                            being.weapon = item
                            field.remove(loc, item)
                            field.text.append('%s picked up %s' % (being.kind, item.description))
                        self.program = None

                if len(items) > 1:
                    if any( [ i!=self or i.kind!="empty" for i in items ] ):
                        self.program = None

                field.display()
        return move_result


    def fullpath(self, loc):
        """ Build shortest path using field.vertices if direct path is blocked.

            First try to find path without vertices that surround each monster.
            Then with one vertice for each monster. Then with all vertices.
        """
        if self.path_list and (self.refresh_path_counter > 0):
            self.refresh_path_counter -= 1
            self.path_list = self.path_list[1:]
            return self.path_list
        origin = self.loc
        path = field.path(origin, loc)

        # save time, set refresh counter and only re-gen path when it's 0
        if self.path_list:
            if len(self.path_list) > 10:
                self.refresh_path_counter = 4
            seed1 = random.choice(range(3,5))
            seed2 = random.choice(range(2,4))
            self.refresh_path_counter = len(self.path_list)/seed1 - seed2

        self.path_list = field.fullpath(origin, loc)
        return self.path_list

    def enter_tactical(self, target):
        """Enter tactical mode."""

        if self.team == "monsters":
            level.attacking_monster = level.monsters.index(self)
            am_kind = self.kind
        if target.team == "monsters":
            log("attack() - target: %s %s" % (target.kind, target))
            log("attack() - level.monsters: %s" % str(level.monsters))
            level.attacking_monster = level.monsters.index(target)
            am_kind = target.kind

        log("level.attacking_monster: %s" % level.attacking_monster)
        level.save_monsters = deepcopy(level.monsters)
        log("level.save_monsters: %s" % level.save_monsters)
        cur = levels.current
        levels.list[cur] = field.fld, level.down, level.up
        field.load_map("local")
        if conf.xmax<10:
            field.blank()
        conf.mode = "tactical"
        level.populate(am_kind)

        while True:
            loc = field.random()
            if not field.next_to(loc, "wall"):
                break
        level.hoplite.place(loc)

        # very rarely a hero may be placed next to a wall,
        for hero in [level.fencer, level.mage]:
            for x in range(100):
                max_dist = random.randint(1,8)
                rloc = field.random()
                if (field.distance(loc, rloc) <= max_dist) and not field.next_to(rloc, "wall"):
                    break
            hero.place(rloc)

        field.full_display()

    def attack(self, target):
        """Attack target."""
        log("attack(): self.kind, target.kind: %s, %s" % (self.kind, target.kind))
        if self.team == target.team:
            return

        if conf.mode == "strategical":
            self.enter_tactical(target)
            return

        # alert target
        if target.program:
            target.program = None

        attack = self.attack_val

        # attack with weapon
        if self.weapon:
            attack += self.weapon.attack
            attack_text = ' with %s [%d]' % (self.weapon.kind, self.weapon.attack)
        else:
            attack_text = ''

        # attack armored foe
        defense = target.defense_val
        defense_text = ''
        if target.armor:
            defense += target.armor.defense
            defense_text = ' (protected by %s armor [%d])' % (target.armor.description, target.armor.defense)

        # cast a blow
        rand = random.random()
        mod = (attack*rand/1.5 - defense*rand/2.0)
        mod = max(0, mod)
        target.health -= round(mod)

        kill = ''
        if target.health <= 0:
            kill = "and killed him"
        field.text.append('%s%s hit %s%s for %d hp %s' % (self.kind,
            defense_text, target.kind, attack_text, mod, kill))

        # if killed
        if target.health <= 0:
            self.experience += target.health + target.attack_val + target.defense_val
            target.die()

    def move_program(self, count):
        """Create a program to move in given direction (count) times."""
        log("- - in move_program()")
        field.status(count)
        c = field.scr.getch()
        if 48 <= c <= 57:
            # example: 22l
            count = int('%d%d' % (count, c-48))
            field.status(count)
            c = field.scr.getch()
        if str(c) in conf.directions:
            self.program = (count, c)

    def go(self, distance=99):
        """ Create a direction movement program.
            example: gk - go up until hit something.
        """
        field.status('g')
        c = field.scr.getch()
        if str(c) in conf.directions:
            self.program = (distance, c)

    def remove(self):
        """Remove from field."""
        field.remove(self.loc, self)
        level.last_index += 1   # ???
        field.redraw(self.loc)
        if self in level.monsters:
            level.monsters.remove(self)

    def die(self):
        """Stop living."""
        self.alive = 0
        field.remove(self.loc, self)
        corpse = Item('corpse', level.last_index)
        level.last_index += 1
        field.set(self.loc, corpse)
        field.redraw(self.loc)
        if self in level.monsters:
            level.monsters.remove(self)

    def next_to(self, kind):
        """Am I close to an object of given type."""
        rc = field.next_to(self.loc, kind)
        log("- next_to(): rc = %s" % rc)
        return rc

    def auto_combat(self):
        """ Try to defeat enemies automatically, without spending time
            if they're too weak to pose a challenge. Applies to all hero
            party.. need to move to PyQuest? or Party?..
        """
        hero_strength = monster_strength = 0
        for hero in [level.hoplite, level.fencer, level.mage]:
            hero_strength += (hero.health + hero.attack_val + hero.defense_val)
        for monster in level.monsters:
            monster_strength += (monster.health + monster.attack_val + monster.defense_val)

        if hero_strength < monster_strength*2:
            field.text.append("Monsters are far too strong!")
            return
        else:
            conf.auto_combat = True
            for hero in [level.hoplite, level.fencer, level.mage]:
                hero.experience += monster_strength
            ratio = hero_strength / float(monster_strength)

            if 2 <= ratio < 3:
                dmg = 0.25
            elif 3 <= ratio < 4:
                dmg = 0.2
            elif 4 <= ratio < 5:
                dmg = 0.15
            elif 5 <= ratio < 6:
                dmg = 0.1
            elif 6 <= ratio < 7:
                dmg = 0.05
            elif 7 <= ratio < 8:
                dmg = 0.03
            else:
                dmg = 0.015

            for hero in [level.hoplite, level.fencer, level.mage]:
                hdmg = dmg * hero.max_health
                hero.health -= hdmg
                hero.health = max(hero.health, 2)
            field.text.append("The party of heroes wins this battle...")


    def special_attack(self):
        """ Special - positional attack. Can only be used by mage and depends on position
            of other team and target.
        """

        log("--- in special_attack()")
        if not self.kind == "mage":
            field.text.append("Only mage can perform special attacks.")
            return
        for name, a_dict in conf.special_attacks.items():
            log("--- checking attack '%s'" % name)
            a_moves1 = a_dict["ally1"]
            a_moves2 = a_dict["ally2"]
            t_moves = a_dict["target"]
            rotations = [[a_moves1, a_moves2, t_moves]]
            # add 3 more rotations
            for i in range(1, 4):
                am1 = copy(a_moves1)
                am2 = copy(a_moves2)
                tm = copy(t_moves)
                for x in range(i):
                    am1 = field.rotate_moves(am1)
                    am2 = field.rotate_moves(am2)
                    tm = field.rotate_moves(tm)
                rotations.append([am1, am2, tm])

            no = True
            for (am1, am2, tm) in rotations:
                log("--- rotation: '%s'" % str((am1, am2, tm)))

                for a_mv in (am1, am2):
                    log("--- a_mv: '%s'" % str(a_mv))
                    a_loc = field.get_loc(self.loc, a_mv)
                    log("--- a_loc: '%s'" % str(a_loc))
                    items = field[a_loc]
                    no = True
                    for i in items:
                        log("--- w.kind: '%s'" % str(w.kind))
                        if i.kind in ("hoplite", "fencer"):
                            no = False
                    if no:
                        log("no!")
                        break
                    else:
                        log("pass!")
                t_loc = field.get_loc(self.loc, tm)
                items = field[t_loc]
                no = True
                monster = None
                for i in items:
                    if i.alive and (i.team == "monsters"):
                        monster = i
                        if name.startswith("arrow"):
                            if "magical" in monster.specials:
                                no = False
                        elif name == "trap":
                            if "animal" in monster.specials:
                                log("--- animal in monster.specials")

                                no = False
                        else:
                            no = False
                if no:
                    log("target: no!")
                else:
                    log("target: pass!")
                    break

            # this special attack can't be done now, let's continue checking other attacks
            if no:
                continue

            log("- special_attack(): name = %s" % name)

            # we can perform this special attack!
            if name.startswith("arrow"):
                dmg = random.randint(5,15)
                attack_text = " with Arrow of Punishment"
            elif name == "trap":
                dmg = random.randint(5,15)
                attack_text = " with Trap of Hunter"
            elif name == "arc":
                dmg = random.randint(5,15)
                attack_text = " with Arc of Electrocution"

            monster.health -= dmg
            kill = ""
            if monster.health <= 0:
                kill = "and killed him"
            field.text.append('%s hit %s%s for %d hp %s' %
                              (self.kind, monster.kind, attack_text, dmg, kill))
            if monster.health <= 0:
                monster.die()

    def advance(self):
        """Advance to new level if enough xp."""
        if self.experience >= self.level_points[self.level+1]:
            self.level += 1
            self.health += random.randint(1,3)
            self.defense_val += random.randint(1,3)
            self.attack_val += random.randint(1,3)
            field.text.append('%s advanced to level %d' % (self.kind, self.level))
