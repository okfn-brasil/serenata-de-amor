#!/usr/bin/env python
"""
The Django app from this repo has a command to load Serenata de Amor datasets
to the app's database. As this is a huge amount of data to be loaded in one
command (specially in production), this Python script runs the command with the
optional arguments to sequentially load 5,000 records during each execution.
"""
from itertools import chain
from math import ceil
from subprocess import call
from sys import argv

TOTAL = 2072729
PER_EXECUTION = 5 * 1000
ROUNDS = ceil(TOTAL / PER_EXECUTION)
COMMAND = ('python', 'manage.py', 'loaddatasets')

try:
    START_FROM_ROUND = int(argv[1])
except IndexError:
    START_FROM_ROUND = 1


for count in range(ROUNDS):
    if (count + 1) > (START_FROM_ROUND - 1):
        start_at = (PER_EXECUTION * count) + 1
        start = ('--start', str(start_at))
        limit = ('--limit', str(PER_EXECUTION))
        drop = ('-d',) if start_at == 1 else ()

        msg1 = '\n==> Round {:,} of {:,}'.format(count + 1, ROUNDS)
        print(msg1)

        msg2 = '    Staring at {:,} and loading {:,} records'
        print(msg2.format(start_at, PER_EXECUTION))

        call(chain(COMMAND, start, limit, drop))
