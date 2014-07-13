""" field.py - map of current level. """

import sys
import math
import random
import conf
import shelve
import curses
import item
import time
import textwrap
from pprint import PrettyPrinter, pformat
from types import *
from collections import defaultdict

import dijkstra
from conf import *
from utils import getitem
from board import Loc
from item import Item
import los

empty_item = Item("empty")

class Field:
    """Map of current level."""

    __shared_state = {}

    def init(self, scr):
        """Setup curses, color pairs, create blank map list."""

        self.__dict__ = self.__shared_state
        self.fld = []   # list of map locations

        # setup curses
        self.scr = scr
        curses.noecho()
        curses.cbreak()
        self.scr.keypad(1)

        # init color pairs
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        self.text          = []                   # list of messages to print in status window
        self.text_history  = ['', '', '']         # 500 lines of last messages
        self.logf          = open('log', 'w')     # log file
        self.show_vertices = False                # only show vertices in map editor

        self.last_pause = time.time()
        self.last_los_points = []                 # line of sight points from last update

        # init map
        self.clear_field()
        self.init_last_seen()

    def __getitem__(self, loc):
        x, y = loc
        return self.fld[x][y]

    def __setitem__(self, loc, item):
        x, y = loc
        self.fld[x][y] = item

    def __iter__(self):
        for x in range(conf.xmax):
            for y in range(conf.ymax):
                yield Loc(x+1, y+1)

    def get_last_seen(self, loc):
        x, y = loc
        return self.last_seen[x][y]

    def set_last_seen(self, loc, item):
        x, y = loc
        self.last_seen[x][y] = item

    def clear_field(self):
        self.fld = []   # list of map locations
        for x in range(conf.xmax+1):
            self.fld.append( [[Item("empty")]] * (conf.ymax+1) )

    def init_last_seen(self):
        self.last_seen = []   # list of last seen items at locations
        for x in range(conf.xmax+1):
            self.last_seen.append( [Item("empty")] * (conf.ymax+1) )

    def valid(self, loc):
        return loc.x >= 1 and loc.y >= 1 and loc.x <= conf.xmax and loc.y <= conf.ymax

    def empty_locs(self):
        return [loc for loc in self if not self.blocked(loc)]

    def neighbour_locs(self, loc):
        """Return the list of neighbour locations of `tile`."""
        x, y = loc
        coords = (-1,0,1)
        locs = set((x+n, y+m) for n in coords for m in coords) - set( [(x,y)] )
        return [ Loc(*tup) for tup in locs if self.valid(Loc(*tup)) ]

    def wrap(self, lst, width):
        return [ l for line in lst for l in textwrap.wrap(line, width) ]

    def log(self, obj):
        """Write obj to log file."""
        # ??? why not using conf.log?
        if isinstance(obj, (list, dict)):
            self.logf.write(PrettyPrinter().pformat(obj))
        else:
            self.logf.write(str(obj) + '\n')
        self.logf.flush()

    def ask(self):
        """Ask a question."""
        if self.question:
            q      = self.question[0]
            q      = q.split('\n')
            q      = self.wrap(q, 79)
            height = len(q) + 2
            width  = max( [len(line) for line in q] )
            win    = curses.newwin(height, width, 23-height, 0)

            for i in range(len(q)):
                win.addstr(i, 0, q[i])
            ans = win.getch()
            # TODO why is 'ans' an int??
            # print('ans', repr(ans))
            del win
            self.scr.touchwin()     # to paint over deleted window
            self.scr.refresh()
            # ans = int(ans) if ans.isdigit() else None

            self.log("ans: %s, right_ans: %s" % (ans, self.question[1]))

            # TODO: should not return right ans
            if ans-48 == self.question[1]:
                self.question = []
                return True
            else:
                right_ans = self.question[2]
                self.question = []
                return right_ans

    def msg(self):
        """Show message (self.text) in the status bar."""
        if self.text:
            self.text = self.wrap(self.text, 79)
            width = max([len(line) for line in self.text])
            self.text_history.extend(self.text)
            # trim history to 500 lines
            self.text_history = self.text_history[-500:]

            if len(self.text) > 3:
                height = len(self.text) + 3
                self.msgwin = curses.newwin(height, width, 20-height, 0)
                for i in range(len(self.text)):
                    self.msgwin.addstr(i, 0, self.text[i])
                self.msgwin.addstr(i+3, 0, 'Hit Enter key..')
                self.msgwin.getch()
                del self.msgwin
                self.scr.touchwin()     # to paint over deleted window

            self.scr.refresh()
            self.text = []

        if self.text_history:
            width = conf.xmax
            self.msgwin = curses.newwin(3, width, 20, 0)
            for n in range(3):
                args = [n, 0]
                line = self.text_history[n-3]
                if isinstance(line, tuple):
                    colpair = curses.color_pair(line[1])
                    args.extend( [line[0], colpair] )
                else:
                    args.append(line)
                self.msgwin.addstr(*args)
            self.msgwin.refresh()
        self.log("--")

    def random_map(self):
        """Load random level map."""
        name = random.choice(maps)
        self.load_map(name)

    def load_map(self, name):
        """Load level map."""
        s = shelve.open("maps")
        self.fld = s[name]
        return
        # make list of vertices
        # self.vertices = []
        # for x in range(xmax+1):
        #     for y in range(ymax+1):
        #         items = self[(x+1,y+1)]
        #         for item in items:
        #             if item.kind == "vertice":
        #                 self.vertices.append((x+1,y+1))

    def status(self, text):
        """Show text in status bar. (trimmed to 79 chars)."""
        self.scr.addstr(23, 0, ' '*79)
        self.scr.addstr(23, 0, str(text)[:79])
        self.scr.refresh()

    def quit(self, msg=None):
        """Quit game."""
        # end curses
        curses.echo()
        curses.nocbreak()
        self.scr.keypad(0)
        curses.endwin()

        if msg:
            print()
            print(msg)
        sys.exit()

    # UNUSED
    def NObeings_vertices(self, one=0):
        """ Return a list of vertices surrounding each monster and hero.

            If one is set, find only one vertice for each monster. (speeds
            things up)
        """

        lst = []
        from level import level     # need to import here to avoid cycle ref.
        beings = level.monsters + [level.hero]

        # add four surrounding squares
        for b in beings:
            loc = b.loc
            if loc.x+1 <= conf.xmax:
                lst.append((loc.x+1, loc.y))
            if loc.x-1 > 0:
                lst.append((loc.x-1, loc.y))
            if loc.y+1 <= conf.ymax:
                lst.append((loc.x, loc.y+1))
            if loc.y-1 > 0:
                lst.append((loc.x, loc.y-1))

        # remove blocked squares
        lst2 = []
        for loc in lst:
            if self[loc]:
                item = self[loc][-1]
                if not item.block:
                    lst2.append(loc)
        if one:
            return lst[:1]
        return lst2

    def blank(self):
        """Put empty instance in all cells."""
        self.clear_field()

    def full_display(self, beings=None, los=True):
        """Redraw tiles at `points`, or all cells if points=None."""
        log( "in full_display()")
        # for l in self:
            # log(l, self[l])

        los_points = list(self.los_update(beings))
        points = los_points if los else iter(self)

        # we need to clear out beings that are no longer visible from being shown
        for loc in self.last_los_points:
            if loc not in los_points:
                item = self.get_last_seen(loc)
                # if item.kind!='empty':
                    # log("clear, item, loc", item, loc)
                if item.alive:
                    self.set_last_seen(loc, empty_item)
                    points.append(loc)

        for loc in points:
            item = self.get_last_seen(loc)
            self.scr.addstr(loc.y-1, loc.x-1, str(item), curses.color_pair(item.color))

        self.display(beings)
        self.last_los_points = los_points

    def los_update(self, beings):
        """Update line-of-sight data."""
        visible = set()
        if beings and not isinstance(beings, list):
            beings = [beings]

        for being in (beings or []):
            visible = los.los(being.loc, 6, self)
            # log("visible", visible)
            for loc in visible:
                ls = self.get_last_seen(loc)
                item = getitem(self[loc], -1, Item("empty"))

                itype='bug'
                if ls.kind==itype and item.kind!=itype:
                    log("moved party FROM loc", loc)
                if ls.kind!=itype and item.kind==itype:
                    log("moved party TO loc", loc)
                self.last_seen[loc.x][loc.y] = item
        return visible

    def display(self, beings=None):
        """Refresh screen."""
        self.los_update(beings)
        self.scr.refresh()

    def blocked2(self, path):
        """Is location blocked?"""
        for loc in path:
            item = getitem(self[loc], -1)
            if item and item.block:
                return True

    def blocked(self, loc):
        """Is location blocked?"""
        item = getitem(self[loc], -1)
        return item and item.block

    def distance(self, loc1, loc2):
        """ Approximate distance, use to see which of several points is
            closer to a given point, for example..
        """
        loc1 = getattr(loc1, "loc", loc1)
        loc2 = getattr(loc2, "loc", loc2)
        dist = abs(loc2.x-loc1.x)**2 + abs(loc2.y-loc1.y)**2
        return int(math.sqrt(dist))

    def set(self, loc, item):
        """ Put item in location on the map.

            return codes:
            False   - out of bounds
            1       - successful move
            3       - blocked by terrain
            4       - successfull move but cell is not empty
        """
        if not self.valid(loc):
            return False

        # check if we can put item there..
        current = self[loc]
        some_obj = False
        if current:
            current = current[-1]
            if current.alive and item.alive:
                return current
            elif current.block:
                return 3
            else:
                some_obj = True

        self[loc].append(item)
        if some_obj:
            return 4
        return 1

    def remove(self, loc, object):
        """Remove object from location."""
        items = self[loc]
        log("remove(): object.kind = %s" % object.kind)
        for item in items:
            log("remove(): item.kind = %s" % item.kind)
            # because 'empty' objects do not have index var
            if item.kind not in ("empty", "vertice"):
                if object.index == item.index:
                    items.remove(item)
                    break

    def rm_kind(self, loc, kind):
        """Remove all objects of this kind."""
        for item in self[loc]:
            if item.kind == kind:
                self.remove(loc, item)

    def pop(self, loc):
        """Remove & return top object at location."""
        if self[loc]:
            return self[loc].pop()

    def random(self):
        """Return random unoccupied cell's location."""
        return random.choice(self.empty_locs())

    def next_to(self, loc, kind):
        """ Is location close to an item of given type? Close here means that the
            item is either at location or right next to it. Later change to give distance,
            optionally?
        """
        x, y = loc
        for tx in (x-1, x, x+1):
            for ty in (y-1, y, y+1):
                items = self[(tx,ty)]
                for item in items:
                    if item.kind == kind:
                        return True

    def get_loc(self, origin, moves):
        """ Get a location by performing a series of moves from origin. This is
            used by being.special_attack() to find out if a special attack is valid
            for current locations of party and monsters. Example:
            get_loc((5,5), (("right", 1), ("up", 1)))   => (6,6)
            Note that only "right", "up", "down", "left" directions are possible.
        """
        x, y = origin
        for dir, dist in moves:
            if dir == "up":
                # note that 0 is top of screen and then it increases as it goes down
                y -= dist
            elif dir == "right":
                x += dist
            elif dir == "down":
                y += dist
            elif dir == "left":
                x -= dist
        return Loc(x, y)


    def rotate_moves(self, move_list):
        """ Rotate moves clockwise 90 degrees. This is used by being.special_attack()
            to check if current location of party and monsters matches one of the special
            attack formations, since formations are described in only one of four possible
            orientations, special_attack() rotates them 3 times.

            Example: rotate_moves( [("up", 1), ("right", 1)] ) => [("right", 1), ("down", 1)]
        """
        lst = []
        for (dir, dist) in move_list:
            if dir == "up":
                lst.append(("right", dist))
            elif dir == "right":
                lst.append(("down", dist))
            elif dir == "down":
                lst.append(("left", dist))
            elif dir == "left":
                lst.append(("up", dist))
        return lst

    def contains(self, loc, kind):
        """Return true if location contains item of given kind."""
        for item in self[loc]:
            if item.kind == kind:
                return True

    def get_coords(self, loc, direction):
        """ Returns coordinates of a cell adjacent to our cell in given direction.
            example: if we're at 1,1 and direction is l (right), return 1,2.
        """
        direction = int(direction)
        (x, y) = loc
        if direction == 108: x += 1         # right
        if direction == 107: y -= 1         # down
        if direction == 104: x -= 1         # left
        if direction == 106: y += 1         # up
        if direction == 98:  x -= 1; y += 1 # left + up
        if direction == 110: x += 1; y += 1 # right + up
        if direction == 121: x -= 1; y -= 1 # left + down
        if direction == 117: x += 1; y -= 1 # right + down
        return Loc(x, y)

    def get_dir(self, from_loc, to_loc):
        """ What is the direction from location to the location? Direction is one of:
            (98, 104, 106, 107, 108, 110, 117, 121) - direction codes in curses.
        """
        mx, my = from_loc
        x, y = to_loc
        if my == y:
            if x > mx:
                return 108
            else:
                return 104
        elif mx == x:
            if y > my:
                return 106
            else:
                return 107
        elif y > my:
            if x > mx:
                return 110
            else:
                return 98
        elif y < my:
            if x > mx:
                return 117
            else:
                return 121


    def get_rev_dir(self, from_loc, to_loc):
        """Get direction using get_dir() and reverse it."""
        dir = self.get_dir(from_loc, to_loc)
        if dir == 108:
            return 104
        elif dir == 104:
            return 108
        elif dir == 107:
            return 106
        elif dir == 106:
            return 107
        elif dir == 98:
            return 117
        elif dir == 117:
            return 98
        elif dir == 110:
            return 121
        elif dir == 121:
            return 110

    def redraw(self, loc):
        # log("= = redraw(): loc, %s" % str(loc))
        items = self[loc]
        if items:
            if items[-1].kind == "vertice":
              # if vertice is on top, the cell must be empty
                item = Item("empty")
            else:
                item = items[-1]
        else:
            item = Item("empty")
        # log("= = redraw(): item, '%s'" % str(item))
        self.scr.addstr(loc.y-1, loc.x-1, str(item), curses.color_pair(item.color))

    def fullpath(self, loc1, loc2):
        """find shortest path, arguments in form (x,y)."""
        path = self.path(loc1, loc2)
        passable = lambda _loc: not self.blocked(_loc) or _loc in (loc1, loc2)
        blocked_path = any([not passable(l) for l in path])
        # log("loc2", loc2)
        # log("blocked_path", blocked_path)
        # log([l for l in path if not passable(l) ])

        # if self.distance(loc1, loc2) > 1 and blocked_path:
        if blocked_path:
            shortest = self.find_shortest(loc1, loc2)
            # log("shortest", shortest)
            if not shortest:
                return []
            return shortest
        return path

    def in_box(self, box, loc):
        """ Return True if `loc` is within the bounding `box`, including box's borders; 

            `box` consists of two points: upper left and lower right.
        """
        p1, p2 = box
        return p1.x <= loc.x <= p2.x and p1.y <= loc.y <= p2.y

    def find_shortest(self, origin, target, extra_vertices=None):
        """Find shortest path using given vertices and static level vertices."""
        nodes = defaultdict(dict)
        origin = getattr(origin, "loc", origin)
        target = getattr(target, "loc", target)

        # make a surrounding box (larger by 3 tiles in each direction than origin/target locations) as an
        # optimization to make dijkstra algorithm faster
        minx, maxx = min(origin.x, target.x), max(origin.x, target.x)
        miny, maxy = min(origin.y, target.y), max(origin.y, target.y)
        minx, maxx = max(0, minx-3), min(xmax, maxx+3)
        miny, maxy = max(0, miny-3), min(ymax, maxy+3)
        p1, p2 = Loc(minx, miny), Loc(maxx, maxy)

        # for dijkstra path alg, consider origin and destination as passable
        passable = lambda _loc: _loc in (origin, target) or not self.blocked(_loc)
        locs = [l for l in self if self.in_box((p1,p2), l)]
        locs = filter(passable, locs)

        for loc in locs:
            nlst = filter(passable, self.neighbour_locs(loc))
            for nloc in nlst:
                dist = 1 if (nloc.x==loc.x or nloc.y==loc.y) else 1.5
                nodes[loc][nloc] = dist

        # log("nodes", pformat(dict(nodes)))
        # find shortest path
        # log("origin", origin)
        # log("target", target)
        try:
            shortest = dijkstra.shortestPath(nodes, origin, target)
            return shortest[1:]
        except KeyError:
            # path is blocked completely
            return []

        return
        vertices = field.vertices + [origin, loc] + extra_vertices
        # make nodes dictionary for dijkstra function; dict is of format
        # {vertice1: {vertice2: distance}}
        for vertice in vertices:
            for vert2 in vertices:
                if vertice != vert2:
                    path = self.path(vertice, vert2)
                    if not self.blocked(path):
                        distance = self.distance(vertice, vert2)
                        if vertice in nodes:
                            nodes[vertice][vert2] = distance
                        else:
                            nodes[vertice] = {vert2: distance}
                        if vert2 in nodes:
                            nodes[vert2][vertice] = distance
                        else:
                            nodes[vert2] = {vertice: distance}

    def path(self, origin, target):
        """ Build navigation path.
            Note: this is a 'dumb' path, it will go over walls and monsters.
        """
        origin = getattr(origin, "loc", origin)
        target = getattr(target, "loc", target)
        x, y   = target
        ox, oy = origin
        path   = []

        # for _ in range(100):
        while True:
            # log(path)
            if (ox, oy) == tuple(target):
                return path
            if x == ox:
                if y > oy:
                    oy += 1
                else:
                    oy -= 1
            elif y == oy:
                if x > ox:
                    ox += 1
                else:
                    ox -= 1
            elif x > ox:
                if y > oy:
                    ox +=1; oy +=1
                else:
                    ox +=1; oy -=1
            elif x < ox:
                if y > oy:
                    ox -=1; oy +=1
                else:
                    ox -=1; oy -=1
            path.append(Loc(ox, oy))


def test():
    moves = conf.special_attacks["trap"]["ally1"]
    print(field.rotate_moves(moves))
    print(field.get_loc((5,5), moves))

field = Field()


if __name__ == "__main__":
    test()
