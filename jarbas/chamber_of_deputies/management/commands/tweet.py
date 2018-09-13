from django.core.management.base import BaseCommand

from jarbas.chamber_of_deputies.twitter import SocialMedia, Twitter


class Command(BaseCommand):
    help = 'Tweet the next suspicion at @RosieDaSerenata'

    def handle(self, *args, **options):
        congressperson_ids_with_twitter = SocialMedia.objects. \
            values_list('congressperson_id', flat=True) \
            .distinct('congressperson_id') \
            .order_by('congressperson_id')

        twitter = Twitter(congressperson_ids_with_twitter)
        if twitter.reimbursement:
            twitter.publish()
