#!/usr/bin/env python
#
# Paramiko Expect Demo Helper
#
# Written by Fotis Gimian
# http://github.com/fgimian
#
# This interactive script is used to help demonstrate the paramiko_expect-demo.py
# script
from __future__ import print_function
import sys


if sys.version_info.major == 3:
    raw_input = input


def main():
    name = raw_input('Please enter your name: ')
    print('Your name is', name)


if __name__ == '__main__':
    main()
