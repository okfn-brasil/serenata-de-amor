from __future__ import print_function

from newrelic.admin import command, usage

@command('generate-config', 'license_key [output_file]',
"""Generates a sample agent configuration file for <license_key>.""")
def generate_config(args):
    import os
    import sys

    if len(args) == 0:
        usage('generate-config')
        sys.exit(1)

    from newrelic import __file__ as package_root
    package_root = os.path.dirname(package_root)

    config_file = os.path.join(package_root, 'newrelic.ini')

    content = open(config_file, 'r').read()

    if len(args) >= 1:
        content = content.replace('*** REPLACE ME ***', args[0])

    if len(args) >= 2 and args[1] != '-':
        output_file = open(args[1], 'w')
        output_file.write(content)
        output_file.close()
    else:
        print(content)
