import lzma

from django.utils.timezone import now
from rows import import_from_csv
from rows.fields import FloatField, TextField

from jarbas.core.fields import DateAsStringField, IntegerField
from jarbas.core.management.commands import LoadCommand
from jarbas.core.models import Reimbursement
from jarbas.core.tasks import create_or_update_reimbursement


class Command(LoadCommand):
    help = 'Load Serenata de Amor reimbursements dataset'

    def handle(self, *args, **options):
        self.started_at = now()
        self.path = options['dataset']

        if options.get('drop', False):
            self.drop_all(Reimbursement)

        self.create_or_update(self.reimbursements)
        self.mark_not_updated_reimbursements()

    @property
    def reimbursements(self):
        """Returns a Generator with a dict object for each row."""
        force_types = {
            'cnpj_cpf': TextField,
            'document_number': TextField,
            'leg_of_the_trip': TextField,
            'congressperson_id': IntegerField,
            'congressperson_document': IntegerField,
            'reimbursement_value_total': FloatField,
            'reimbursement_values': TextField,
            'issue_date': DateAsStringField,
            'term': IntegerField,
            'term_id': IntegerField
        }
        with lzma.open(self.path) as file_handler:
            for row in import_from_csv(file_handler, force_types=force_types):
                as_dict = dict(row._asdict())  # _asdict returns OrderedDict
                yield as_dict

    def create_or_update(self, rows):
        for count, row in enumerate(rows, 1):
            create_or_update_reimbursement.delay(row)
            self.print_count(Reimbursement, count=count)

        print('{} reimbursements scheduled to creation/update'.format(count))

    def mark_not_updated_reimbursements(self):
        qs = Reimbursement.objects.filter(last_update__lt=self.started_at)
        qs.update(available_in_latest_dataset=False)
