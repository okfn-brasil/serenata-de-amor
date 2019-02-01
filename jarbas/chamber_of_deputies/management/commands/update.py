from csv import DictReader, DictWriter
from pathlib import Path
from urllib.request import urlretrieve

from django.core.management import call_command
from django.core.management.base import BaseCommand

from jarbas.chamber_of_deputies.models import Reimbursement, Tweet


class Command(BaseCommand):
    help = (
        'Load Serenata de Amor reimbursements from a given directory. '
        '(1) Does a backup of Twitter data to re-link reimbursements; '
        '(2) Deletes all data from Reimbursement model; '
        '(3) Loads all reimbursements-YYYY.csv files; '
        '(4) Loads suspicions.xz file; '
        '(5) Reload receipt texts; '
        '(6) Rebuilds the search vector;'
        '(7) Restores Twitter data.'
    )
    RECEIPT_TEXTS = '2017-02-15-receipts-texts.xz'
    SPACES_URL = 'https://serenata-de-amor-data.nyc3.digitaloceanspaces.com/'

    def add_arguments(self, parser):
        parser.add_argument('path', help='Directory of the CSV/LZMA files')

    def handle(self, *args, **options):
        self.path = Path(options['path'])

        # (1) Does a backup of Twitter data to re-link reimbursements
        print(f'Backing up {Tweet.objects.count()} tweets')
        with open(self.path / 'tweets.csv', 'w') as fobj:
            writer = DictWriter(fobj, fieldnames=('status', 'document_id'))
            writer.writeheader()
            for tweet in Tweet.objects.all():
                writer.writerow({
                    'status': tweet.status,
                    'document_id': tweet.reimbursement.document_id
                })

        # (2) Deletes all data from Reimbursement model
        # (3) Loads all reimbursements-YYYY.csv files
        first_round = True
        for file in sorted(self.path.glob('reimbursements-*.csv')):
            print(f'Importing {file}')
            call_command('reimbursements', file, drop_all=first_round)
            first_round = False

        # (4) Loads suspicions.xz file
        print(f'Importing {self.path / "suspicions.xz"}')
        call_command('suspicions', self.path / 'suspicions.xz')

        # (5) Reload receipt texts
        urlretrieve(
            f'{self.SPACES_URL}{self.RECEIPT_TEXTS}',
            self.path / self.RECEIPT_TEXTS
        )
        print(f'Importing {self.path / self.RECEIPT_TEXTS}')
        call_command('receipts_text', self.path / self.RECEIPT_TEXTS)

        # (6) Rebuilds the search vector
        print(f'Rebuilding the search vector')
        call_command('searchvector')

        # (7) Restores Twitter data
        print(f'Restoring tweets')
        with open(self.path / 'tweets.csv') as fobj:
            for tweet in DictReader(fobj):
                key = {'document_id': tweet['document_id']}
                try:
                    reimbursement = Reimbursement.objects.get(**key)
                except Reimbursement.DoesNotExist:
                    continue

                Tweet.objects.create(
                    status=tweet['status'],
                    reimbursement=reimbursement
                )
