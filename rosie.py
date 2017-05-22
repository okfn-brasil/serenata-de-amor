from sys import argv, exit


def entered_command(argv):
    if len(argv) >= 2:
        return argv[1]
    return None


def help():
    message = (
        'Usage:',
        '  python rosie.py run chamber_of_deputies [<path to output directory>]',
        'Testing:',
        '  python rosie.py test',
        '  python rosie.py test chamber_of_deputies',
    )
    print('\n'.join(message))


def run():
    import rosie
    import rosie.chamber_of_deputies
    import rosie.federal_senate


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
    import os
    import unittest

    loader = unittest.TestLoader()

    if len(argv) >= 3:
        target_module = argv[2]
        tests_path = os.path.join('rosie', target_module)
        tests = loader.discover(tests_path)
    else:
        tests = loader.discover('rosie')

    testRunner = unittest.runner.TextTestRunner()
    result = testRunner.run(tests)

    if not result.wasSuccessful():
        exit(1)


commands = {'run': run, 'test': test}
command = commands.get(entered_command(argv), help)
command()
