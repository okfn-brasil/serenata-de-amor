import csv
import os

from jarbas.core.management.commands import LoadCommand
from jarbas.chamber_of_deputies.models import SocialMedia


class Command(LoadCommand):
    help = 'Load congresspeople social media accounts'
    count = 0

    def handle(self, *args, **options):
        self.path = options['dataset']
        if not os.path.exists(self.path):
            raise FileNotFoundError(os.path.abspath(self.path))

        if options.get('drop', False):
            self.drop_all(SocialMedia)

        print('Saving social media accounts')
        with open(self.path) as fobj:
            bulk = (SocialMedia(**line) for line in csv.DictReader(fobj))
            SocialMedia.objects.bulk_create(bulk)
            print('Done!')
