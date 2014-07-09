#!/usr/bin/env python

# Imports {{{
""" pyquest.py  main file

BUGS:
    1. sometimes being.fullpath() returns path that walks over walls.
           bug #1 sometimes makes beings jump over walls.
    2. path finding algorithm is slow when there are many monsters on the map.
    3. g<dir> "go" commands loses you one move.

"""

import sys
import time
import random
import curses
import types
from copy import copy

import conf
from being import Being
from item import Item
from field import field
from level import level
from levels import levels
from weapon import Weapon
from conf import log
from board import Loc
#from kinds import kinds
# }}}


# Vars {{{
__version__ = "0.1b"
lose_msg    = "\nYou Die."
win_msg     = "\nYou Win."
test        = False
ask_chance  = .95      # checked against random() call

# translation of curses key codes to key values
keymap = {
    97  : 'a',
    113 : 'q',
    103 : 'g',
    62  : '>',
    60  : '<',
    65  : 'A',
    115 : 's',
}

commands = {
    'q' : "field.quit",       # quit program
    'g' : "cur_being.go",     # e.g. 'gl' will go all the way to the left
    '>' : "cur_being.down",
    '<' : "cur_being.up",
    'A' : "cur_being.auto_combat",
    's' : "cur_being.special_attack",
    'a' : "cur_being.attack_closest_monster",
}
# }}}


def move(level_num):
    """ Move all monsters.

        Heal monsters, update status msg, auto-move them.
    """

    for being in level.monsters:
        if being.alive:
            being.heal()

            # move using autopilot
            if being.program:
                times, direction = being.program
                rval = being.move(direction)
                if type(rval) == type(being):
                    # live monster there..
                    being.attack(rval)

                # program may have been reset in being.move()
                if being.program:
                    times -= 1
                    if not ok or ok in (2,3) or times < 1:
                        # bumped into something or end of program
                        being.program = None
                    else:
                        being.program = times, direction

            else:

                if conf.mode == "strategical":
                    dist = field.distance(level.hero, being)
                elif conf.mode == "tactical":
                    dist_h = field.distance(level.hoplite, being)
                    dist_f = field.distance(level.fencer, being)
                    dist_m = field.distance(level.mage, being)
                    dist = min(dist_h, dist_f, dist_m)

                if dist < 9 and being.hostile:
                    being.attack_hero_flag = True

                    if conf.mode == "strategical":
                        dist = field.distance(being, level.hero)
                        if dist == 1:
                            being.attack(level.hero)
                        else:
                            # moves closer to hero
                            being.attack_hero()

                    elif conf.mode == "tactical":
                        if dist_h == dist:
                            who = level.hoplite
                            being.attack_hero(level.hoplite)
                        elif dist_f == dist:
                            who = level.fencer
                            being.attack_hero(level.fencer)
                        else:
                            who = level.mage
                        dist = field.distance(being, who)

                        if dist == 1:
                            being.attack(who)
                        else:
                            # moves closer to hero
                            being.attack_hero(who)

                else:
                    being.random_move()

    if not level.monsters:
        if levels.current+1 >= conf.levels:
            win = curses.newwin(2, 70, 21, 0)
            win.addstr(0,0, "Victory is yours!")
            win.addstr(1,0, "Press any key to end game..")
            win.getch()
            sys.exit()


def health_bar():
    """ Print health status bar showing health of all 3 heroes, encoded in color,
        yellow and red, if health is low.
        It will look like:
        (lev %d) (H %d/%dHP) (F %d/%dHP) (M %d/%dHP)
    """

    h, f, m = level.hoplite, level.fencer, level.mage
    lst = []
    lst.append( ("(lev %d) " % levels.current, 1) )

    # Hoplite
    lst.append( ("(H ", 1) )
    color = 1
    health = float(h.health) / h.max_health
    if   health <= 0.16: color = 4
    elif health <= 0.3: color = 7
    lst.append( ("%d" % h.health, color) )
    lst.append( ("/%dHP) " % h.max_health, 1) )

    # Fighter
    lst.append( ("(F ", 1) )
    color = 1
    if float(f.health) / f.max_health <= 0.16:
        color = 4   # red
    elif float(f.health) / f.max_health <= 0.3:
        color = 7   # yellow
    lst.append( ("%d" % f.health, color) )
    lst.append( ("/%dHP) " % f.max_health, 1) )

    # Mage
    lst.append( ("(M ", 1) )
    color = 1
    if float(m.health) / m.max_health <= 0.16:
        color = 4   # red
    elif float(m.health) / m.max_health <= 0.3:
        color = 7   # yellow
    lst.append( ("%d" % m.health, color) )
    lst.append( ("/%dHP) " % m.max_health, 1) )

    offset = 0
    field.scr.addstr(23, 0, ' '*79)
    for (s, col) in lst:
        field.scr.addstr(23, offset, s, col)
        offset += len(s) + 1

class PyQuest:
    def __init__(self, scr):
        self.scr = scr
        conf.logf = open("log.txt", "w")
        field.init(scr)
        field.blank()
        self.main()

    def test_special_attacks(self):
        level_num = 1
        field.load_map("local")
        level.hero = Being('party', field.random(), level.last_index)
        level.last_index += 1
        # level.hero.place()
        level.hoplite = Being("hoplite", Loc(36,10), level.last_index)
        level.hoplite.place()
        level.last_index += 1
        level.fencer = Being("fencer", Loc(35,10), level.last_index)
        level.fencer.place()
        level.last_index += 1
        level.mage = Being("mage", Loc(35,11), level.last_index)
        level.mage.place()
        level.last_index += 1

        t = Being("troll", Loc(34,9), level.last_index)
        t.team = "monsters"
        t.place()
        level.monsters = [t]
        level.last_index += 1
        conf.mode = "tactical"

    def main(self):
        """ Main loop.
            Create hero's team; move them; create new levels when old ends.
        """
        level_num = 1
        field.load_map("empty")
        level.populate()

        # make hero's party
        level.hero = Being('party', field.random(), level.last_index)
        level.last_index += 1
        level.hero.place()
        level.hoplite = Being("hoplite", Loc(1,1), level.last_index)
        level.last_index += 1
        level.fencer = Being("fencer", Loc(1,2), level.last_index)
        level.last_index += 1
        level.mage = Being("mage", Loc(1,3), level.last_index)
        level.last_index += 1

        field.full_display()

        # game loop
        while True:
            time.sleep(0.01)

            monster = level.hero.find_closest_monster()

            if conf.mode == "strategical":
                party = [level.hero]
            elif conf.mode == "tactical":
                party = [level.hoplite, level.fencer, level.mage]
            level.hoplite.heal()
            level.fencer.heal()
            level.mage.heal()

            all_near_wall = True
            for cur_being in party:
                if not cur_being.alive:
                    continue
                if not level.monsters and conf.mode == "tactical" and not test:
                    break

                if cur_being.program:
                    log("- - cur being (%s) has a program.." % cur_being.kind)
                    times, direction = cur_being.program
                    ok = cur_being.move(direction)
                    # program may have been reseted in being.move()
                    if cur_being.program:
                        log("- - cur being STILL has a program..")
                        times -= 1
                        if (not ok) or (times < 1):
                            # bumped into something or end of program
                            cur_being.program = None
                            log("- - resetting program because bumped into something?..")
                        else:
                            cur_being.program = times, direction
                else:
                    health_bar()
                    # log("- - cur being (%s) has NO program..\n" % cur_being.kind)
                    loc = cur_being.loc
                    # log("kind: %s, x: %d y: %d;\n" % (cur_being.kind, x, y))
                    field.display()
                    field.scr.move(loc.y-1, loc.x-1)
                    c = field.scr.getch()
                    if c in keymap.keys():
                        exec(commands[keymap[c]] + '()')
                    elif 49 <= c <= 57:
                        # e.g. '5l' moves 5 times to the left
                        cur_being.move_program(c-48)
                    move_res = cur_being.move(c)
                    if type(move_res) == type(cur_being):
                        # live monster
                        monster = move_res
                        # cur_being.attack(monster)
                        if conf.mode == "strategical" and random.random() < ask_chance and not monster.asked:
                            monster.ask(cur_being)
                        else:
                            cur_being.attack(monster)

                # check if all party is near a wall in tactical mode:
                if conf.mode == "tactical":
                    all_near_wall = True
                    party = [level.hoplite, level.fencer, level.mage]
                    for hero in party:
                        log("checking hero: %s" % (hero.kind))
                        if not hero.next_to("wall"):
                            log("hero: %s is NOT close to a wall." % (hero.kind))
                            all_near_wall = False
                            break
                        else:
                            log("hero: %s IS close to a wall." % (hero.kind))
                        hero.advance()
                    if all_near_wall or conf.auto_combat:
                        break
                field.msg()


            log("loop: all_near_wall: %s" % all_near_wall)
            if ((not level.monsters or all_near_wall or conf.auto_combat) and
                                    conf.mode == "tactical" and not test):
                we_won = False
                if not level.monsters or conf.auto_combat:
                    we_won = True
                cur = levels.current
                field.fld, level.down, level.up = levels.list[cur]
                conf.mode = "strategical"
                level.monsters = level.save_monsters

                # killed the monster team..
                level.hero.program = None
                attacker = level.monsters[level.attacking_monster]
                if we_won:
                    attacker.die()
                else:
                    # we need to try to move away from the enemy (running away!!)
                    dir = field.get_rev_dir(level.hero.location, attacker.location)
                    level.hero.move(dir)
                conf.auto_combat = False
                field.full_display()
            else:
                move(level_num)

            field.display()
            field.msg()
            #field.msgwin.getch()


# pyq = PyQuest()
curses.wrapper(PyQuest)
