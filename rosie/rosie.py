#!/usr/bin/env python

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from rosie import chamber_of_deputies, federal_senate


def main():
    parser = ArgumentParser(description='''Artificial Intelligence for social control of public administration''',
            epilog='''Example: rosie.py chamber-of-deputies''',
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('module', nargs='?', default='all',
        help='a module to run, could be chamber-of-deputies or federal-senate')
    parser.add_argument('--dataset', '-d', nargs='?',
        help='the source dataset')
    args = parser.parse_args()
    if ('chamber-of-deputies' in args.module) or args.module == 'all':
        if args.dataset:
            chamber_of_deputies.main(args.dataset)
        else:
            chamber_of_deputies.main()
    if ('federal-senate' in args.module) or args.module == 'all':
        if args.dataset:
            federal_senate.main(args.dataset)
        else:
            federal_senate.main()


if __name__ == '__main__':
    main()
