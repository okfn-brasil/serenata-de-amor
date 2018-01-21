import optparse
import sys

from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.utils.module_loading import import_string


HELP = 'Tells Django to NOT use migrations and create all tables directly.'


TestCommand = import_string(getattr(
    settings,
    'TEST_WITHOUT_MIGRATIONS_COMMAND',
    'django.core.management.commands.test.Command'))


# testserver command only exists on Django 1.10+
if DJANGO_VERSION >= (1, 10):
    TestServerCommand = import_string(
        'django.core.management.commands.testserver.Command'
    )
else:
    TestServerCommand = TestCommand


class DisableMigrations(object):

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        # django 1.9 takes None, 1.7/8 has an error here, so use a dummy value
        # 1.11+ always actually imports the module, so we can't use the dummy there
        if DJANGO_VERSION < (1, 9):
            return 'notmigrations'
        else:
            return None


class CommandMixin(object):

    def __init__(self):
        super(CommandMixin, self).__init__()

        # Optparse was deprecated on 1.8
        # So we only define option_list for Django 1.7
        if DJANGO_VERSION < (1, 8):
            self.option_list = super(CommandMixin, self).option_list + (
                optparse.make_option(
                    '-n',
                    '--nomigrations',
                    action='store_true',
                    dest='nomigrations',
                    default=False,
                    help=HELP),
            )

    def add_arguments(self, parser):  # New API on Django 1.8
        super(CommandMixin, self).add_arguments(parser)

        parser.add_argument(
            '-n',
            '--nomigrations',
            action='store_true',
            dest='nomigrations',
            default=False,
            help=HELP)

    def handle(self, *test_labels, **options):
        for arg in ('-n', '--nomigrations'):
            if arg in sys.argv:
                sys.argv.remove(arg)

        if options['nomigrations']:
            settings.MIGRATION_MODULES = DisableMigrations()

        super(CommandMixin, self).handle(*test_labels, **options)
