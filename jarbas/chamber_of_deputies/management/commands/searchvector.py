from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector

from tqdm import tqdm

from jarbas.chamber_of_deputies.models import Reimbursement


class Command(BaseCommand):

    BATCH_SIZE = 4096

    def add_arguments(self, parser):
        parser.add_argument('--silent', dest='silent', action='store_true')
        parser.add_argument(
            '--all', action='store_true',
            dest='all_reimbursements',
            help='Re-create all search vectors'
        )
        parser.add_argument(
            '--batch-size', '-b', dest='batch_size', type=int,
            default=self.BATCH_SIZE,
            help='Batch size for bulk update (default: 4096)'
        )

    def handle(self, *args, **options):
        batch_size = options.get('batch_size', self.BATCH_SIZE)
        silent = options.get('silent')
        all_reimbursements = options.get('all_reimbursements')

        queryset = Reimbursement.objects.filter(search_vector=None)
        if all_reimbursements:
            queryset = Reimbursement.objects.all()

        if not queryset.exists():
            return

        search_vector = \
            SearchVector('congressperson_name', config='portuguese', weight='A') + \
            SearchVector('supplier', config='portuguese', weight='A') + \
            SearchVector('cnpj_cpf', config='portuguese', weight='A') + \
            SearchVector('party', config='portuguese', weight='A') + \
            SearchVector('state', config='portuguese', weight='B') + \
            SearchVector('receipt_text', config='portuguese', weight='B') + \
            SearchVector('passenger', config='portuguese', weight='C') + \
            SearchVector('leg_of_the_trip', config='portuguese', weight='C') + \
            SearchVector('subquota_description', config='portuguese', weight='D') + \
            SearchVector('subquota_group_description', config='portuguese', weight='D')

        pks = tuple(obj['pk'] for obj in queryset.values('pk'))
        total = len(pks)

        if not silent:
            print(f'Creating search vector for {total} reimbursements…')

        kwargs = {
            'total': total,
            'desc': 'Reimbursements',
            'unit': 'vector',
            'disable': silent
        }
        with tqdm(**kwargs) as progress_bar:
            for start in range(0, total, batch_size):
                end = min(start + batch_size, total)
                Reimbursement.objects \
                    .filter(pk__in=pks[start:end]) \
                    .update(search_vector=search_vector)
                progress_bar.update(end - start)
