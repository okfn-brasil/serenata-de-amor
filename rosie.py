from sys import argv, exit


def entered_command(argv):
    if len(argv) >= 2:
        return argv[1]
    return None


def help():
    message = (
        'Usages:',
        '  python rosie.py run chamber_of_deputies [<path to output directory>]',
        '  python rosie.py test',
    )
    print('\n'.join(message))


def run():
    import rosie, rosie.chamber_of_deputies
    if len(argv) >= 3:
        target_module = argv[2]
    else:
        print('A module must be provided.')
        help()
        exit(1)
    target_directory = argv[3] if len(argv) >= 4 else '/tmp/serenata-data/'
    klass = getattr(rosie, target_module)
    klass.main(target_directory)


def test():
    import unittest
    loader = unittest.TestLoader()
    tests = loader.discover('rosie')
    testRunner = unittest.runner.TextTestRunner()
    testRunner.run(tests)


commands = {'run': run, 'test': test}
command = commands.get(entered_command(argv), help)
command()
