from concurrent import futures
from time import sleep

from bulk_update.helper import bulk_update
from django.core.management.base import BaseCommand
from requests.exceptions import ConnectionError

from jarbas.core.models import Reimbursement


class Command(BaseCommand):
    help = 'Fetch receipts URLs from Chamber of Deputies server'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size', '-b', dest='batch_size', type=int, default=256,
            help='Requests before pause (prevent blocking, default: 256)'
        )
        parser.add_argument(
            '--pause', '-p', dest='pause', type=int, default=2,
            help='Pause length in seconds (default: 2)'
        )

    def handle(self, *args, **options):
        self.batch, self.pause = options['batch_size'], options['pause']
        self.count = 0
        self.queue = []

        print('Loading…')
        self.queryset = self.get_queryset()

        if self.queryset:
            while self.queryset:
                self.fetch()
                self.queryset = self.get_queryset()
                if self.queryset:
                    self.print_pause()
                    sleep(self.pause)
            else:
                self.print_count(permanent=True)
                print('Done!')
        else:
            print('Nothing to fetch.')

    def fetch(self):
        with futures.ThreadPoolExecutor(max_workers=32) as executor:
            for result in executor.map(self.update, self.queryset):
                self.count += 1
                self.print_count()
        self.bulk_update()

    def bulk_update(self):
        self.print_saving()
        fields = ['receipt_url', 'receipt_fetched']
        bulk_update(self.queue, update_fields=fields)
        self.queue = []

    def get_queryset(self):
        return Reimbursement.objects.filter(receipt_fetched=False)[:self.batch]

    def update(self, reimbursement):
        try:
            obj = reimbursement.get_receipt_url(bulk=True)
        except ConnectionError:
            pass
        else:
            self.queue.append(obj)

    @staticmethod
    def print_msg(msg, permanent=False):
        if not permanent:
            cursor_up_one = '\x1b[1A'
            erase_line = '\x1b[2K'
            print('{}{}{}'.format(cursor_up_one, erase_line, cursor_up_one))
        print(msg)

    def count_msg(self):
        return '{:,} receipt URLs fetched'.format(self.count)

    def print_count(self, **kwargs):
        return self.print_msg(self.count_msg(), **kwargs)

    def print_pause(self, **kwargs):
        pause_msg = '{} (Taking a break to avoid being blocked…)'
        return self.print_msg(pause_msg.format(self.count_msg()), **kwargs)

    def print_saving(self, **kwargs):
        saving_msg = '{} (Saving the URLs to the database…)'
        return self.print_msg(saving_msg.format(self.count_msg()), **kwargs)
