from django.core.management.base import BaseCommand

from jarbas.chamber_of_deputies.twitter import Twitter


class Command(BaseCommand):
    help = 'Tweet the next suspicion at @RosieDaSerenata account'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fake',
            action='store_true',
            help='Do not tweet, just show the tweet message'
        )

    def handle(self, *args, **options):
        twitter = Twitter()
        if not twitter.reimbursement:
            print('No suspicion to tweet')
            return None

        if options.get('fake'):
            print(twitter.message)
            return None

        twitter.publish()
