from unittest.mock import Mock, call, patch

from django.test import TestCase
from django.db.models import QuerySet

from jarbas.core.management.commands.receipts import Command


class TestCommandHandler(TestCase):

    @patch('jarbas.core.management.commands.receipts.Command.get_queryset')
    @patch('jarbas.core.management.commands.receipts.Command.fetch')
    @patch('jarbas.core.management.commands.receipts.print')
    def test_handler_with_queryset(self, print_, fetch, get_queryset):
        get_queryset.return_value = True
        command = Command()
        command.handle(batch_size=42, pause=1)
        print_.assert_called_once_with('Loading…', end='\r')
        get_queryset.assert_called_once_with()
        fetch.assert_called_once_with()
        self.assertEqual(42, command.batch)
        self.assertEqual(1, command.pause)
        self.assertEqual(0, command.count)

    @patch('jarbas.core.management.commands.receipts.Command.get_queryset')
    @patch('jarbas.core.management.commands.receipts.Command.fetch')
    @patch('jarbas.core.management.commands.receipts.print')
    def test_handler_without_queryset(self, print_, fetch, get_queryset):
        get_queryset.return_value = False
        command = Command()
        command.handle(batch_size=42, pause=1)
        print_.assert_has_calls([
            call('Loading…', end='\r'),
            call('Nothing to fetch.')
        ])
        get_queryset.assert_called_once_with()
        fetch.assert_not_called()
        self.assertEqual(42, command.batch)
        self.assertEqual(1, command.pause)
        self.assertEqual(0, command.count)

    def test_add_arguments(self):
        parser = Mock()
        command = Command()
        command.add_arguments(parser)
        self.assertEqual(2, parser.add_argument.call_count)


class TestCommandMethods(TestCase):

    @patch('jarbas.core.management.commands.receipts.Command.update')
    @patch('jarbas.core.management.commands.receipts.Command.get_queryset')
    @patch('jarbas.core.management.commands.receipts.sleep')
    @patch('jarbas.core.management.commands.receipts.print')
    def test_fetch(self, print_, sleep, get_queryset, update):
        get_queryset.side_effect = (
            (1, 2, 3),
            (4, 5, 6),
            (7, 8, 9),
            (10,),
            ()
        )

        command = Command()
        command.count = 0
        command.batch = 3
        command.pause = 42
        command.queryset = command.get_queryset()
        command.fetch()

        print_calls = (
            call('1 receipt URLs fetched                                         ', end='\r'),
            call('2 receipt URLs fetched                                         ', end='\r'),
            call('3 receipt URLs fetched                                         ', end='\r'),
            call('3 receipt URLs fetched (Taking a break to avoid being blocked…)', end='\r'),
            call('4 receipt URLs fetched                                         ', end='\r'),
            call('5 receipt URLs fetched                                         ', end='\r'),
            call('6 receipt URLs fetched                                         ', end='\r'),
            call('6 receipt URLs fetched (Taking a break to avoid being blocked…)', end='\r'),
            call('7 receipt URLs fetched                                         ', end='\r'),
            call('8 receipt URLs fetched                                         ', end='\r'),
            call('9 receipt URLs fetched                                         ', end='\r'),
            call('9 receipt URLs fetched (Taking a break to avoid being blocked…)', end='\r'),
            call('10 receipt URLs fetched                                         ', end='\r'),
            call('10 receipt URLs fetched                                         ', end='\n'),
            call('Done!')
        )

        get_queryset.aeert_has_calls(call() * 4)
        update.assert_has_calls(call(i) for i in range(1, 11))
        self.assertEqual(10, command.count)
        print_.assert_has_calls(print_calls)
        sleep.assert_has_calls([call(42)] * 3)

    @patch.object(QuerySet, '__getitem__')
    @patch.object(QuerySet, 'filter', return_value=QuerySet())
    def test_get_queryset(self, filter_, getitem):
        command = Command()
        command.batch = 42
        command.get_queryset()
        filter_.assert_called_once_with(receipt_fetched=False)
        getitem.assert_called_once_with(slice(None, 42))

    def test_update(self):
        reimbursement = Mock()
        Command.update(reimbursement)
