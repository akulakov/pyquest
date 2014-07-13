#!/usr/bin/env python3

import os, sys

def main():
    while True:
        i = input('> ') or 'def '
        if i=='q':
            break
        os.system("grep '%s' *.py" % i)
        print('='*78)

main()
