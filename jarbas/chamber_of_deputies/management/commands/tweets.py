import logging
import re

import twitter
from django.conf import settings
from django.core.management.base import BaseCommand

from jarbas.chamber_of_deputies.models import Reimbursement, Tweet


class Command(BaseCommand):
    help = 'Find out and save links to @RosieDaSerenata tweets'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.credentials = (
            settings.TWITTER_CONSUMER_KEY,
            settings.TWITTER_CONSUMER_SECRET,
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_SECRET
        )
        self.log = logging.getLogger('django')

    def handle(self, *args, **options):
        if not all(self.credentials):
            self.log.warning('Twitter API credentials not set.')
            return

        # persist tweet status in the database
        for status, document_id in self.document_ids:

            # skip if reimbursement does not exist
            kwargs = dict(document_id=document_id)
            try:
                reimbursement = Reimbursement.objects.get(**kwargs)
            except Reimbursement.DoesNotExist:
                continue

            # skip if status is already related to that reimbursement
            try:
                current_tweet = reimbursement.tweet
            except Tweet.DoesNotExist:
                pass
            else:
                if current_tweet.status == status:
                    continue

            self.save_tweet(reimbursement, status)

    @property
    def tweets(self):
        """
        Generator yielding the last tweets (200 is the API limit) since the
        last tweet saved in Jarbas database. If no tweet is saved it yields the
        last 200 tweets.
        """
        kwargs = dict(
            screen_name='RosieDaSerenata',
            count=200,  # this is the maximum suported by Twitter API
            include_rts=False,
            exclude_replies=True
        )

        latest_tweet = Tweet.objects.first()
        if latest_tweet:
            kwargs['since_id'] = latest_tweet.status

        api = twitter.Api(*self.credentials, sleep_on_rate_limit=True)
        yield from api.GetUserTimeline(**kwargs)

    @property
    def urls(self):
        """
        Generator that iterates self.tweets and yields a tuple with the Twitter
        status ID (int) and the URL (str) tweeted in that tweet. In case a
        single tweet has more than one URL more than one tuple will be yielded
        for that tweet.
        """
        for tweet in self.tweets:
            yield from ((tweet.id, url.expanded_url) for url in tweet.urls)

    @staticmethod
    def get_document_id(url):
        """
        Gets a URL (str) and return the Reimbursement document ID (int)
        contained in it. If nothing is found, or document ID is not an `int`
        returns None.
        """
        match = re.search(r'documentId\/(?P<document_id>\d*)', url)
        try:
            return int(match.group('document_id'))
        except (AttributeError, ValueError):
            return None  # AttributeError (no match) or ValueError (not an int)

    @property
    def document_ids(self):
        """
        Generator that consumes self.urls and yields a tuple with Tweet Status
        ID (int) and Reimbursement document ID (int). It skips tweets URLs that
        don't contain avalid reimbursement URL.
        """
        for tweet_id, url in self.urls:
            document_id = self.get_document_id(url)
            if document_id:
                yield tweet_id, document_id

    def save_tweet(self, reimbursement, status):
        """
        :param reimbursement: Reimbursement instance
        :param status: (int) Tweet status ID
        """
        if Tweet.objects.filter(reimbursement=reimbursement):
            msg = 'Document #{} already linked to {}'
        else:
            Tweet.objects.create(reimbursement=reimbursement, status=status)
            msg = 'Document #{} just linked to {}'

        args = (reimbursement.document_id, reimbursement.tweet.get_url())
        self.log.info(msg.format(*args))
