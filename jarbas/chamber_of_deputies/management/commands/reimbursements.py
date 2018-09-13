from csv import DictReader

from jarbas.core.management.commands import LoadCommand
from jarbas.chamber_of_deputies.models import Reimbursement
from jarbas.chamber_of_deputies.tasks import serialize


class Command(LoadCommand):
    help = 'Load Serenata de Amor reimbursements dataset'
    BATCH_SIZE = 4096

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--batch-size', '-b', dest='batch_size', type=int,
            default=self.BATCH_SIZE,
            help='Batch size for bulk update (default: 4096)'
        )

    def handle(self, *args, **options):
        self.path = options['dataset']
        self.batch_size = options.get('batch_size', self.BATCH_SIZE)
        self.batch, self.count = [], 0

        if options.get('drop', False):
            self.drop_all(Reimbursement)

        self.create_batches()

    @property
    def reimbursements(self):
        """Returns a Generator with a Reimbursement instance for each row."""
        with open(self.path, 'rt') as file_handler:
            for row in DictReader(file_handler):
                obj = serialize(row)
                if obj:
                    yield obj

    def create_batches(self):
        for count, reimbursement in enumerate(self.reimbursements, 1):
            self.count = count
            self.batch.append(reimbursement)
            if len(self.batch) >= self.batch_size:
                self.persist_batch()
        self.persist_batch(print_permanent=True)

    def persist_batch(self, print_permanent=False):
        Reimbursement.objects.bulk_create(self.batch)
        self.batch = []
        self.print_count(
            Reimbursement,
            count=self.count,
            permanent=print_permanent
        )
