#!/usr/bin/env python3

from __future__ import division
from functools import total_ordering
from collections import defaultdict
from random import choice, randrange, random, randint
import math

import conf
from conf import xmax, ymax

from board import Loc
from utils import first

# docstring {{{
"""Rooms and corridors.

###-----
###    |
###   ###
      ###
      ###

###
###----*
###    |
###    ##
      ####
       ##

 ####
######
######
 ####

  ##
 ####
######
 ####
  ##

######
######
######
######

######
##  ##
######

######
######
##  ##
######
######

    #
   ##
  ###
 ####
#####

# 0  ##
# 1 ####
# 2######
# 3 ####
# 4  ##

"""

"""
* pick a y from y range of room1, pick an x from x range of room 2
* burrow down to room2, burrow to left to room1
* check if we intersect any other corridors
"""

updir, downdir, rgtdir, leftdir = (0,-1), (0,1), (1,0), (-1,0)
# }}}

class Limit:
    def __init__(self, x_axis, y_axis, level):
        self.x1, self.x2 = x_axis
        self.y1, self.y2 = y_axis
        self.level = level
        self.children = []

    def __repr__(self):
        return str( (self.x2-self.x1) * (self.y2-self.y1) )

    @property
    def container(self):
        """Convert limit dimensions to a container."""
        return (self.x1, self.y1), (self.x2, self.y2)


class Rooms:
    def __init__(self):
        self.containers = []
        self.rooms      = []
        self.corridors  = []
        self.limits     = []
        self.max_rooms  = randint(3, randint(5, randint(7, 10)))
        # self.max_rooms = 2

    def make_limits(self, limit=None, level=0):
        """ Limits for rooms.

            limit: pair of x-axis tuple and a y-axis tuple
            level: level of recursion, e.g. at 0 level board contains 1 limit, at lev1, divided into 2 limits,
                at lev2, divided into 4, etc
        """
        limit      = limit or ((1, xmax+1), (1, ymax+1))
        xrng, yrng = limit
        x1, x2     = xrng
        y1, y2     = yrng

        if (x2-x1)<4 or (y2-y1)<4:
            return
        self.limits.append( Limit(*limit, level=level) )

        x_done, y_done = (x2-x1)<9, (y2-y1)<9
        if x_done and y_done:
            return

        # if y_done, do x, if x_done, do y, otherwise pick random one
        if y_done or not x_done and random()>.5:
            new_x = randrange(x1+4, x2-3)
            lim1  = (x1, new_x), (y1, y2)
            lim2  = (new_x+1, x2), (y1, y2)
        else:
            new_y = randrange(y1+4, y2-3)
            lim1  = (x1, x2), (y1, new_y)
            lim2  = (x1, x2), (new_y+1, y2)
        level += 1
        self.make_limits(lim1, level)
        self.make_limits(lim2, level)

    def make_containers(self):
        """ Make room containers out of the list of limits.
            Choose the level depending on `max_rooms` number, use limits at that level to create room
            containers.
        """
        limit_dict = defaultdict(list)
        for lim in self.limits:
            limit_dict[lim.level].append(lim)

        level = 1
        while True:
            nlimits = len(limit_dict[level])
            if not nlimits:
                break
            limits = limit_dict[level][:self.max_rooms]
            if nlimits >= self.max_rooms:
                break
            level += 1

        self.containers = [lim.container for lim in limits]

    def make_rooms(self):
        id = 1
        for (x1,y1), (x2,y2) in self.containers:
            rx1 = randint(x1+1, x2-3)
            rx2 = randint(rx1+1, x2-1)

            # ginormous rooms should be rare
            if (rx2-rx1)>20 and random()>.1:
                rx2 = rx1 + 20
            if (rx2-rx1)==1:
                rx2 += 1

            s, e = y1+1, y2-3   # start, end
            half = s + (e-s)//2
            # print("s,e,half", s,e,half)
            # push first point closer to start
            ry1 = randint(s, randint(half, e))

            s, e = ry1+1, y2-1
            half = s + (e-s)//2
            # print("s,e,half", s,e,half)
            # push second point closer to end
            ry2 = randint(randint(s, half), e)

            if (ry2-ry1)>20 and random()>.1:
                ry2 = ry1 + 20
            if (ry2-ry1)==1:
                ry2 += 1
            self.rooms.append( Room((rx1,ry1), (rx2,ry2), id) )
            id += 1
        self.rooms.sort()

    def burrow_points(self, loc, dirs, x_fin, y_fin):
        """ Return borrow points, used to tell if connecting corridor will interfere with other rooms or
            corridors.

            loc   : start location
            dirs  : tuple of directions where a dir is e.g. 0,1 for 'right'
            x_fin : terminate x dir at `x_fin` (similarly for `y_fin`)
        """
        start = loc
        points = []
        for dir in dirs:
            if dir[0] in (1,-1):
                x, y = loc
                step = dir[0]
                lst = range(x, x_fin+step, step)
                points.extend( [Loc(x, y) for x in lst] )
            elif dir[1] in (1,-1):
                x, y = loc
                step = dir[1]
                lst = range(y, y_fin+step, step)
                points.extend( [Loc(x, y) for y in lst] )

        return points

    def burrow(self, start, dirs):
        for dir in dirs:
            loc = start
            while True:
                if invalid(self.fld, loc.y, loc.x):
                    break
                tile = self.fld[loc.y][loc.x]
                # print("loc.x,loc.y", loc.x,loc.y)
                # print("tile", tile)
                if tile == ' ' and loc != start:
                    break
                self.fld[loc.y][loc.x] = ' '
                loc = loc.moved(*dir)

    def dist(self, r1, r2):
        l1, l2 = r1.center(), r2.center()
        return math.sqrt( abs(l2.x - l1.x)**2 + abs(l2.y - l1.y)**2  )

    def closest(self, room, rooms):
        dist = lambda _room: self.dist(room, _room)
        return first(sorted(rooms, key=dist))

    def make_corridors(self, fld):
        self.fld = fld
        # connected = [self.rooms[0]]
        room = self.rooms[0]
        rooms = self.rooms[1:]
        print("room", room)
        # print("rooms", rooms)
        while rooms:
            room2 = self.closest(room, rooms)
            to_remove = room2
            print("closest: room2", room2)

            room, room2 = sorted([room, room2])
            x_rng, y_rng = room.range_intersect(room2)
            print("x_rng,y_rng", x_rng,y_rng)

            if x_rng:
                x = randint(*x_rng)
                # y = min(room.y2, room2.y2)
                # print("x,y", x,y)
                self.burrow( Loc(x, room.y2+1), [updir, downdir] )
            elif y_rng:
                x = min(room.x2, room2.x2)
                y = randint(*y_rng)
                print("y", y)
                self.burrow( Loc(x+1, y), [leftdir, rgtdir] )

            else:
                if room.x1 < room2.x1:
                    # room orientation:
                    # R
                    #  R2
                    dirs = leftdir, downdir
                    # step = 1
                    fin_x = room.x2+1
                else:
                    #    R
                    #  R2
                    dirs = rgtdir, downdir
                    # room, room2 = room2, room
                    # step = -1
                    fin_x = room.x1-1
                print("room.center()", room.center(), room)
                print("room2.center()", room2.center(), room2)

                x_rng = room2.offset_ranges()[0]
                y_rng = room.offset_ranges()[1]
                print("x_rng,y_rng", x_rng,y_rng)
                print("room.x2", room.x2)
                x1 = max(room.x2+2, x_rng[0])
                # x_rng = (x1, x_rng[1])
                x = randint(*x_rng)

                print("room2.y2", room2.y2)
                y1 = max(room2.y2+2, y_rng[0])
                # y_rng = (y_rng[1], y1)
                y = randint(*y_rng)
                start = Loc(x,y)
                pts = self.burrow_points(start, dirs, fin_x, room2.y1-1)
                for p in pts:
                    if not is_rock(self.fld, p):
                        print('not rock', p)
                if all(is_rock(self.fld, p) for p in pts):
                    self.burrow(start, dirs)
                else:
                    print("Error making the corridor")

            # if room2 in rooms:
            print("rooms", rooms)
            print("room2", room2)
            rooms.remove(to_remove)
            room = to_remove
            # break


def is_rock(fld, loc):
    return fld[loc.y][loc.x] == '.'

def invalid(fld, y, x):
    return y<0 or x<0 or y>=len(fld) or x>=len(fld[0])

class Room:
    def __init__(self, p1, p2, id=1):
        self.p1           = p1
        self.p2           = p2
        self.x1, self.y1  = p1
        self.x2, self.y2  = p2
        self.special_type = None
        self.id           = id
        self.special()

    def __lt__(self, room):
        return self.center().y < room.center().y

    def __repr__(self):
        return "ID:%s | p1:%s p2:%s" % (self.id, self.p1, self.p2)

    @property
    def xsize(self):
        return self.x2 - self.x1

    @property
    def ysize(self):
        return self.y2 - self.y1

    def center(self):
        (x1,y1),(x2,y2) = self.p1, self.p2
        return Loc(x1 + (x2-x1)/2, y1 + (y2-y1)/2)

    def offset_ranges(self):
        """Inclusive ranges."""
        # return (self.x1+1, self.x2-1), (self.y1+1, self.y2-1)
        return (self.x1, self.x2), (self.y1, self.y2)

    def range_intersect(self, room):
        """Return tuple (x_range_intersect, y_range_intersect)."""
        (x1_1, x1_2), (y1_1, y1_2) = self.offset_ranges()
        (x2_1, x2_2), (y2_1, y2_2) = room.offset_ranges()

        x1 = max(x1_1, x2_1)
        x2 = min(x1_2, x2_2)
        y1 = max(y1_1, y2_1)
        y2 = min(y1_2, y2_2)
        yield (x1,x2) if (x2-x1)>=0 else None
        yield (y1,y2) if (y2-y1)>=0 else None
        # return xrng, yrng

    def make_inside_points(self):
        x1, x2 = self.x1, self.x2
        y1, y2 = self.y1, self.y2
        points = []
        for y in range(self.ysize+1):
            points.append([x for x in range(self.xsize+1)])

        # round corners by 1 point
        if self.special_type == 1:
            del points[self.ysize][self.xsize]
            del points[self.ysize][0]
            del points[0][self.xsize]
            del points[0][0]

        # rhombus shape
        if self.special_type == 2:
            n = self.ysize // 2
            for y, row in enumerate(points):

                m = n-y if y<n else \
                        n - (self.ysize-y)

                if m>0:
                    del row[-m-1:]
                    del row[:m]

        # triangle
        if self.special_type == 3:
            left = randint(0,1)
            for y, row in enumerate(points):
                m = self.ysize-y
                if m>0:
                    if left:
                        del row[:m]
                    else:
                        del row[-m-1:]

        for y, row in enumerate(points):
            for x in row:
                yield y1+y, x1+x

    def special(self):
        if self.xsize>=5 and self.ysize>=5 and self.xsize==self.ysize:
            self.special_type = 3   # triangle
        elif self.xsize>=6 and self.ysize>=5 and random()>.3:
            self.special_type = 2   # rhombus
        elif (self.xsize>=4 or self.ysize>=4) and random()>.8:
            self.special_type = 1   # rounded corners


def test():
    xm,ym=79,20
    lim = (1, xm), (1, ym)
    from pprint import pprint
    from copy import deepcopy
    from string import ascii_letters

    fld = []
    for _ in range(ym+1):
        fld.append( ['.'] * (xm+1) )

    for _ in range(0):
        r=Rooms()
        r.make_limits(lim)
        r.make_containers()
        r.make_rooms()
        r.make_corridors(fld)
        # print(len(r.containers))
    # return

    rooms = Rooms()
    rooms.make_limits(lim)
    rooms.make_containers()
    rooms.make_rooms()
    # pprint(r.containers)
    for r in rooms.rooms:
        points = r.make_inside_points()
        for y,x in points:
            fld[y][x] = ' '
    rooms.make_corridors(fld)

    f = fld
    n = 0
    for (x1,y1), (x2,y2) in rooms.containers:
        # print("x1,y1", x1,y1)
        # print("x2,y2", x2,y2)
        # f = deepcopy(fld)

        # f[y1][x1] = ascii_letters[n]
        # f[y2][x2] = ascii_letters[n]
        n+=1
        # for row in f[1:]:
        #     row = ''.join(row[1:])
        #     print(row)
        # if input('> ')=='q': break

    for row in fld[:]:
        row = ''.join(row[:])
        print(row)


if __name__ == "__main__":
    test()
