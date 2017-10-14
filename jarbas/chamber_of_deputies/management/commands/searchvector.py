from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector

from jarbas.chamber_of_deputies.models import Reimbursement


class Command(BaseCommand):

    def handle(self, *args, **options):
        total = Reimbursement.objects.count()
        print('Creating search vector for {} reimbursements…'.format(total))
        print('This takes several minutes/hours.')

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

        Reimbursement.objects.update(search_vector=search_vector)
