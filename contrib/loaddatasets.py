
#!/usr/bin/env python
"""
The Django app from this repo has a command to load Serenata de Amor datasets
to the app's database. As this is a huge amount of data to be loaded in one
command (specially in production), this Python script runs the command with the
optional arguments to sequentially load 1000 records during each execution.
"""
from itertools import chain
from math import ceil
from subprocess import call
from time import sleep

TOTAL = 2072729
PER_EXECUTION = 1000
ROUNDS = ceil(TOTAL / PER_EXECUTION)
COMMAND = ('heroku', 'run', 'python', 'manage.py', 'loaddatasets')


for count in range(ROUNDS):
    start_at = (PER_EXECUTION * count) + 1
    start = ('--start', str(start_at))
    limit = ('--limit', str(PER_EXECUTION))

    msg1 = '==> Round {} of {}'.format(count + 1, ROUNDS)
    print(msg1)

    msg2 = '    Staring at {} and loading {} records'
    print(msg2.format(start_at, PER_EXECUTION))

    call(chain(COMMAND, start, limit))

    print('==> Sleeping for 1min                                             ')
    sleep(60)
