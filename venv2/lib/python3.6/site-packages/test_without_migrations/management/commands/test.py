from test_without_migrations.management.commands._base import CommandMixin, TestCommand


class Command(CommandMixin, TestCommand):
    pass
