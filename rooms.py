#!/usr/bin/env python3

from __future__ import division
from functools import total_ordering
from collections import defaultdict
from random import choice, randrange, random, randint
import conf
from conf import xmax, ymax

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
            print("s,e,half", s,e,half)
            # push first point closer to start
            ry1 = randint(s, randint(half, e))

            s, e = ry1+1, y2-1
            half = s + (e-s)//2
            print("s,e,half", s,e,half)
            # push second point closer to end
            ry2 = randint(randint(s, half), e)

            if (ry2-ry1)>20 and random()>.1:
                ry2 = ry1 + 20
            if (ry2-ry1)==1:
                ry2 += 1
            self.rooms.append( Room((rx1,ry1), (rx2,ry2)) )
        self.rooms.sort()

    def make_corridors(self):
        connected = [self.rooms[0]]
        room = self.rooms[0]
        for room2 in self.rooms[1:]:
            x_rng, y_rng = room.range_intersect(room2)
            if x_rng:
                x = randint(x_rng)


class Room:
    def __init__(self, p1, p2):
        self.p1           = p1
        self.p2           = p2
        self.x1, self.y1  = p1
        self.x2, self.y2  = p2
        self.special_type = None
        self.special()

    def __lt__(self, room):
        return self.center() < room.center()

    @property
    def xsize(self):
        return self.x2 - self.x1

    @property
    def ysize(self):
        return self.y2 - self.y1

    def center(self):
        return (self.x2-self.x1), (self.y2-self.y1)

    def offset_ranges(self):
        return (self.x1+1, self.x2-1), (self.y1+1, self.y2-1)

    def range_intersect(self, room):
        """Return tuple (x_range_intersect, y_range_intersect)."""
        x1 = max(self.x1, room.x1)
        x2 = min(self.x2, room.x2)
        y1 = max(self.y1, room.y1)
        y2 = min(self.y2, room.y2)
        yield (x1,x2) if (x2-x1)>0 else None
        yield (y1,y2) if (y2-y1)>0 else None
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
    xm,ym=80,20
    lim = (1, xm), (1, ym)
    from pprint import pprint
    from copy import deepcopy
    from string import ascii_letters
    for _ in range(0):
        r=Rooms()
        r.make_limits(lim)
        r.make_containers()
        r.make_rooms()
        # print(len(r.containers))
    # return

    rooms = Rooms()
    rooms.make_limits(lim)
    rooms.make_containers()
    rooms.make_rooms()
    # pprint(r.containers)
    fld = []
    for _ in range(ym+1):
        fld.append( ['.'] * (xm+1) )

    for r in rooms.rooms:
        points = r.make_inside_points()
        for y,x in points:
            fld[y][x] = ' '

    f = fld
    n = 0
    for (x1,y1), (x2,y2) in rooms.containers:
        # print("x1,y1", x1,y1)
        # print("x2,y2", x2,y2)
        # f = deepcopy(fld)

        f[y1][x1] = ascii_letters[n]
        f[y2][x2] = ascii_letters[n]
        n+=1
        # for row in f[1:]:
        #     row = ''.join(row[1:])
        #     print(row)
        # if input('> ')=='q': break

    for row in fld[1:]:
        row = ''.join(row[1:])
        print(row)


if __name__ == "__main__":
    test()
