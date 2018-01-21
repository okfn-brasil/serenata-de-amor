from __future__ import print_function

from newrelic.admin import command, usage

@command('debug-console', 'config_file [session_log]',
"""Runs the client for the embedded agent debugging console.
""", hidden=True, log_intercept=False)
def debug_console(args):
    import sys

    if len(args) == 0:
        usage('debug-console')
        sys.exit(1)

    from newrelic.console import ClientShell

    config_file = args[0]
    log_object = None

    if len(args) >= 2:
        log_object = open(args[1], 'w')

    shell = ClientShell(config_file, log=log_object)
    shell.cmdloop()
