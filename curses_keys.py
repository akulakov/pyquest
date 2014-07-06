#!/usr/bin/env python
"""Check to see which num codes correspond to keys in curses."""

import sys
import curses

scr = curses.initscr()
curses.noecho()
curses.cbreak()
scr.keypad(1)

while 1:
    c = scr.getch()
    if c == 113:
        break
    else:
        scr.addstr(0,0,' '*79)
        scr.addstr(0,0,str(c))

curses.echo()
curses.nocbreak()
scr.keypad(0)
curses.endwin()
