from concurrent import futures
from time import sleep

from django.core.management.base import BaseCommand

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

        print('Loading…', end='\r')
        self.queryset = self.get_queryset()

        if self.queryset:
            self.fetch()
        else:
            print('Nothing to fetch.')

    def fetch(self):
        while self.queryset:
            with futures.ThreadPoolExecutor(max_workers=32) as executor:
                for result in executor.map(self.update, self.queryset):
                    self.count += 1
                    self.print_count()

            self.queryset = self.get_queryset()
            if self.queryset:
                self.print_count(pause=True)
                sleep(self.pause)
        else:
            self.print_count(permanent=True)
            print('Done!')

    def get_queryset(self):
        return Reimbursement.objects.filter(receipt_fetched=False)[:self.batch]

    @staticmethod
    def update(reimbursement):
        reimbursement.get_receipt_url()

    def print_count(self, **kwargs):
        pause_msg = 'Taking a break to avoid being blocked…'
        count_msg = '{:,} receipt URLs fetched'.format(self.count)

        if kwargs.get('pause'):
            msg = '{} ({})'.format(count_msg, pause_msg)
        else:
            msg = count_msg + (' ' * (len(pause_msg) + 3))

        end = '\n' if kwargs.get('permanent') else '\r'
        print(msg, end=end)
