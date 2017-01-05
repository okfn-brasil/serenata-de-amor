from unittest.mock import Mock, call, patch

from django.test import TestCase
from django.db.models import QuerySet
from requests.exceptions import ConnectionError

from jarbas.core.management.commands.receipts import Command


class TestCommandHandler(TestCase):

    @patch('jarbas.core.management.commands.receipts.Command.get_queryset')
    @patch('jarbas.core.management.commands.receipts.Command.fetch')
    @patch('jarbas.core.management.commands.receipts.Command.print_count')
    @patch('jarbas.core.management.commands.receipts.Command.print_pause')
    @patch('jarbas.core.management.commands.receipts.sleep')
    @patch('jarbas.core.management.commands.receipts.print')
    def test_handler_with_queryset(self, print_, sleep, print_pause, print_count, fetch, get_queryset):
        get_queryset.side_effect = (True, True, True, False)
        command = Command()
        command.handle(batch_size=3, pause=42)
        print_.assert_has_calls((call('Loading…'), call('Done!')))
        print_pause.assert_has_calls((call(), call()))
        print_count.assert_called_once_with(permanent=True)
        sleep.assert_has_calls([call(42)] * 2)
        self.assertEqual(3, fetch.call_count)
        self.assertEqual(3, command.batch)
        self.assertEqual(42, command.pause)
        self.assertEqual(0, command.count)

    @patch('jarbas.core.management.commands.receipts.Command.get_queryset')
    @patch('jarbas.core.management.commands.receipts.Command.fetch')
    @patch('jarbas.core.management.commands.receipts.print')
    def test_handler_without_queryset(self, print_, fetch, get_queryset):
        get_queryset.return_value = False
        command = Command()
        command.handle(batch_size=42, pause=1)
        print_.assert_has_calls([
            call('Loading…'),
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
    @patch('jarbas.core.management.commands.receipts.Command.bulk_update')
    @patch('jarbas.core.management.commands.receipts.Command.print_count')
    def test_fetch(self, print_count, bulk_update, update):
        command = Command()
        command.count = 0
        command.queryset = (1, 2, 3)
        command.queue = []
        command.fetch()
        print_count.assert_has_calls((call(), call(), call()))
        update.assert_has_calls(call(i) for i in range(1, 4))
        self.assertEqual(3, command.count)
        bulk_update.assert_called_once_with()

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
        command = Command()
        command.queue = []
        command.update(reimbursement)
        reimbursement.get_receipt_url.assert_called_once_with(bulk=True)
        self.assertEqual(1, len(command.queue))

    def test_update_with_error(self):
        reimbursement = Mock()
        reimbursement.get_receipt_url.side_effect = ConnectionError()
        command = Command()
        command.queue = []
        command.update(reimbursement)
        reimbursement.get_receipt_url.assert_called_once_with(bulk=True)
        self.assertEqual(0, len(command.queue))

    @patch('jarbas.core.management.commands.receipts.bulk_update')
    @patch('jarbas.core.management.commands.receipts.Command.print_saving')
    def test_bulk_update(self, print_saving, bulk_update):
        command = Command()
        command.queue = [1, 2, 3]
        command.bulk_update()
        fields = ['receipt_url', 'receipt_fetched']
        bulk_update.assert_called_once_with([1, 2, 3], update_fields=fields)
        self.assertEqual([], command.queue)
        print_saving.assert_called_once_with()


class TestCommandPrintMethods(TestCase):

    def test_count_msg(self):
        command = Command()
        command.count = 42
        self.assertEqual('42 receipt URLs fetched', command.count_msg())

    @patch('jarbas.core.management.commands.receipts.print')
    def test_print_msg(self, print_):
        Command.print_msg('42')
        print_.assert_has_calls((
            call('\x1b[1A\x1b[2K\x1b[1A'),
            call('42')
        ))

    @patch('jarbas.core.management.commands.receipts.print')
    def test_print_permanent_msg(self, print_):
        Command.print_msg('42', permanent=True)
        print_.assert_called_once_with('42')

    @patch('jarbas.core.management.commands.receipts.Command.count_msg')
    @patch('jarbas.core.management.commands.receipts.Command.print_msg')
    def test_print_count(self, print_msg, count_msg):
        count_msg.return_value = '42'
        command = Command()
        command.print_count()
        command.print_count(permanent=True)
        print_msg.assert_has_calls((call('42'), call('42', permanent=True)))

    @patch('jarbas.core.management.commands.receipts.Command.count_msg')
    @patch('jarbas.core.management.commands.receipts.Command.print_msg')
    def test_print_pause(self, print_msg, count_msg):
        count_msg.return_value = '42'
        command = Command()
        command.print_pause()
        print_msg.assert_called_once_with('42 (Taking a break to avoid being blocked…)')

    @patch('jarbas.core.management.commands.receipts.Command.count_msg')
    @patch('jarbas.core.management.commands.receipts.Command.print_msg')
    def test_print_saving(self, print_msg, count_msg):
        count_msg.return_value = '42'
        command = Command()
        command.print_saving()
        print_msg.assert_called_once_with('42 (Saving the URLs to the database…)')
