from django.core.management.base import BaseCommand

from jarbas.core.models import Reimbursement


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('Loading…')
        queryset = Reimbursement.objects.filter(receipt_fetched=False)
        self.count = 0

        for reimbursement in queryset:
            reimbursement.get_receipt_url()
            self.count += 1
            self.print_count()

        self.print_count(permanent=True)
        print('Done!')

    def print_count(self, **kwargs):
        end = '\n' if kwargs.get('permanent') else '\r'
        print('{:,} receipt URLs fetched…'.format(self.count), end=end)
