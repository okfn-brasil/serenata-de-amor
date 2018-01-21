from test_without_migrations.management.commands._base import CommandMixin, TestServerCommand


class Command(CommandMixin, TestServerCommand):
    pass
