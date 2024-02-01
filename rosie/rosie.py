"""
Hi, I am Rosie from Operação Serenata de Amor! 🤖

I'm a proof-of-concept for the usage of artificial intelligence for social
control of public administration.

Usage:
  rosie.py run (chamber_of_deputies|federal_senate) [--output=<directory>] [--last_years=<x>]
  rosie.py test [chamber_of_deputies|federal_senate|core]

Options:
  --help                 Show this screen
  --output=<directory>   Output directory  [default: /tmp/serenata-data]
  --last_years=<x>       Only last X years
"""
import os
import unittest
import logging
from datetime import date

from docopt import docopt

import rosie
import rosie.chamber_of_deputies
import rosie.federal_senate

log = logging.getLogger('rosie')

def get_module(arguments):
    modules = ('chamber_of_deputies', 'federal_senate', 'core')
    for module in modules:
        if arguments[module]:
            return module


def run(module, directory, starting_year):
    module = getattr(rosie, module)
    module.main(starting_year=starting_year, target_directory=directory)


def test(module=None):
    loader = unittest.TestLoader()
    tests_path = 'rosie'

    if module:
        tests_path = os.path.join(tests_path, module)

    tests = loader.discover(tests_path)
    testRunner = unittest.runner.TextTestRunner()
    result = testRunner.run(tests)
    if not result.wasSuccessful():
        exit(1)

def get_starting_year(last_years):
    if last_years:
        return date.today().year - int(last_years) + 1
    else:
        return 2009

def main():
    arguments = docopt(__doc__)
    module = get_module(arguments)

    if arguments['test']:
        test(module)

    if arguments['run']:
        module = module if module != 'core' else None
        starting_year = get_starting_year(arguments['--last_years'])
        log.info(f'Running from {starting_year}')
        run(module, arguments['--output'], starting_year)

    log.info('done')

if __name__ == '__main__':
    main()
