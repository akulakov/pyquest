#!/usr/bin/env python

'''Map editor for I, Monster game.

 class Editor:

     def help(self):
        """Print help message in status."""
     def init_commands(self):
        """Key mappings."""
     def vertice(self):
        """Add vertice."""
     def wall(self):
        """Start wall mode."""
     def move(self):
        """Start move mode."""
     def clear_cell(self):
        """Erase current cell location."""
     def clear_all(self):
        """Erase all cell locations."""
     def save(self):
        """Save current map."""
     def load(self):
        """Load map."""
     def quit(self):
        """Quit map editor."""
     def loop(self):
        """Main ui loop."""
     def get_coords(self, direction):
        """Get coordinates of the next cell in given direction."""

'''

import curses
import shelve
import conf
from field import field
from item import Item


help_msg = """
 v       vertice
 w       wall
 m       move cursor (use hjkl,yubn keys)
 c       clear cell
 C       clear all
 s       save map
 o       load map
 ?       help
 q       quit

 In move and wall modes, you can do this type of commands:

     6l     6 to the left
     gh     all the way to the right
""".split('\n')


class Editor:
    def __init__(self, scr):
        """Initialize field, move cursor to start, load maps, show status,
        start loop."""
        field.init(scr)
        # blanking puts an empty item into each empty cell, this makes maps
        # file 2mb large
        field.blank()
        field.show_vertices = True
        # field module starts coordinations from 1, not 0
        self.location = 1,1
        self.mode = "move"
        #curses.curs_set(2)     # high cursor visibility
        field.scr.move(0,0)
        self.maps = shelve.open('maps')
        self.init_commands()
        field.status("Hit '?' for help.")


    def help(self):
        """Print help message in status."""
        field.text = help_msg
        field.msg()


    def init_commands(self):
        """Key mappings."""

        self.keymap = {
            118     : 'v',
            111     : 'o',
            119     : 'w',
            109     : 'm',
            99      : 'c',
            67      : 'C',
            115     : 's',
            113     : 'q',
            63      : '?',
        }

        self.commands = {
            'v'     : self.vertice,
            'w'     : self.wall,
            'm'     : self.move,
            'c'     : self.clear_cell,
            'C'     : self.clear_all,
            's'     : self.save,
            'o'     : self.load,
            '?'     : self.help,
            'q'     : self.quit,
        }


    def vertice(self):
        """Add vertice."""
        field.set(self.location, Item('vertice'))


    def wall(self):
        """Start wall mode."""
        field.text.append("in wall()")
        # field.status("in wall()")
        # c = field.scr.getch()
        self.mode = 'wall'
        field.set(self.location, Item('wall'))


    def move(self):
        """Start move mode."""
        self.mode = 'move'


    def clear_cell(self):
        """Erase current cell location."""
        items = field[self.location]
        for item in items:
            if item.kind != 'empty':
                field.remove(self.location, item)


    def clear_all(self):
        """Erase all cell locations."""
        for x in range(1, conf.xmax+1):
            for y in range(1, conf.ymax+1):
                self.location = x,y
                self.clear_cell()


    def save(self):
        """Save current map."""
        field.status("Enter the name: ")
        curses.echo()
        name = field.scr.getstr().strip()
        curses.noecho()
        if name:
            self.maps[name] = field.fld


    def load(self):
        """Load map."""
        field.status("Enter name of the map to load: ")
        curses.echo()
        name = field.scr.getstr().strip()
        curses.noecho()
        if name:
            if not self.maps.has_key(name):
                field.text = ["No such map found! (%s)" % name]
                field.msg()
                return
            field.fld = self.maps[name]
            self.location = 1,1
            field.scr.move(0,0)
            field.display()


    def quit(self):
        """Quit map editor."""
        self.maps.close()
        field.quit()


    def loop(self):
        """Main ui loop."""
        go = False  # program movement
        while 1:
            x = None
            if not go:
                c = field.scr.getch()
                field.status(c)
            if c in self.keymap:
                field.status("c is in keymap")
                self.commands[self.keymap[c]]()

            # g<dir>
            elif c == 103:
                go = 99
                c = field.scr.getch()
                continue

            # <num><dir>
            elif 48 <= c <= 57:
                go = c-48
                field.status(go)
                c = field.scr.getch()
                if 48 <= c <= 57:
                    go += int('%d%d' % (go, c-48))
                    c = field.scr.getch()
                continue

            # <dir>
            if str(c) in conf.directions:
                x,y = self.get_coords(c)
                #field.status('%d,%d' % (x,y))
                if x < 1 or x > conf.xmax:
                    go = False
                    continue
                elif y < 1 or y > conf.ymax:
                    go = False
                    continue

                self.location = x,y
                if self.mode == 'wall':
                    items = field[self.location]
                    put_wall = True
                    for item in items:
                        if item.kind == 'wall':
                            put_wall = False
                            break
                    if put_wall:
                        field.set(self.location, Item('wall'))
                if go:
                    go -= 1

            field.full_display()
            lx, ly = self.location
            field.status('%d,%d' % (lx,ly))
            field.msg()
            if x:
                field.scr.move(y-1,x-1)
                field.scr.refresh()


    def get_coords(self, direction):
        """Get coordinates of the next cell in given direction."""
        direction = int(direction)
        (x, y) = self.location
        if direction == 108: x += 1
        if direction == 107: y -= 1
        if direction == 104: x -= 1
        if direction == 106: y += 1
        if direction == 98: x -= 1; y += 1
        if direction == 110: x += 1; y += 1
        if direction == 121: x -= 1; y -= 1
        if direction == 117: x += 1; y -= 1
        return x, y


def main(scr):
    e = Editor(scr)
    e.loop()


if __name__ == "__main__":
    curses.wrapper(main)
