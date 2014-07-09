#!/usr/bin/env python3

import os, sys

def main():
    while True:
        i = input('> ')
        if i=='q':
            break
        os.system("grep '%s' *.py" % i)

main()
