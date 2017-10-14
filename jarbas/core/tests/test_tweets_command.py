from collections import namedtuple
from itertools import permutations
from unittest.mock import MagicMock, PropertyMock, patch

from django.test import TestCase
from mixer.backend.django import mixer

from jarbas.chamber_of_deputies.models import Reimbursement, Tweet
from jarbas.chamber_of_deputies.management.commands.tweets import Command
from jarbas.chamber_of_deputies.tests import random_tweet_status


KEYS = (
    'TWITTER_CONSUMER_KEY',
    'TWITTER_CONSUMER_SECRET',
    'TWITTER_ACCESS_TOKEN',
    'TWITTER_ACCESS_SECRET'
)

Url = namedtuple('Url', ('expanded_url'))
Status = namedtuple('Status', ('id', 'urls'))


class TestCommand(TestCase):

    def setUp(self):
        self.credentials = {k: '42' for k in KEYS}


class TestAuthWithoutCredential(TestCommand):

    @patch('jarbas.chamber_of_deputies.management.commands.tweets.logging.getLogger')
    @patch('jarbas.chamber_of_deputies.management.commands.tweets.twitter.api')
    @patch.object(Tweet.objects, 'first')
    def test_handler_without_credentials(self, first, api, log):
        missing_values = tuple(set(permutations(['', '42', '42', '42'])))
        missing_credentials = (dict(zip(KEYS, v)) for v in missing_values)
        for credentials in missing_credentials:
            with self.settings(**credentials):
                Command().handle()
        api.assert_not_called()
        first.assert_not_called()
        self.assertEqual(4, log.return_value.warning.call_count)


class TestAuthWithCredentials(TestCommand):

    @patch('jarbas.chamber_of_deputies.management.commands.tweets.twitter.Api')
    @patch.object(Tweet.objects, 'first')
    def test_credentials(self, first, api):
        with self.settings(**self.credentials):
            Command().handle()
        credentials = (self.credentials[k] for k in KEYS)
        api.assert_called_once_with(*credentials, sleep_on_rate_limit=True)
        first.assert_called_once_with()


class TestHandle(TestCommand):

    def setUp(self):
        self.credentials = {k: '42' for k in KEYS}

    @patch.object(Command, 'document_ids', new_callable=PropertyMock)
    @patch.object(Command, 'save_tweet')
    def test_non_existent_reimbursement(self, save_tweet, document_ids):
        document_ids.return_value = ((42, 24),)
        with self.settings(**self.credentials):
            Command().handle()
        save_tweet.assert_not_called()

    @patch.object(Command, 'document_ids', new_callable=PropertyMock)
    @patch.object(Command, 'save_tweet')
    def test_existing_tweet(self, save_tweet, document_ids):
        reimbursement = mixer.blend(Reimbursement, search_vector=None, document_id=123456)
        mixer.blend(Tweet, status=42, reimbursement=reimbursement)

        document_ids.return_value = ((42, 123456),)
        with self.settings(**self.credentials):
            Command().handle()
        save_tweet.assert_not_called()

    @patch.object(Command, 'document_ids', new_callable=PropertyMock)
    @patch.object(Command, 'save_tweet')
    def test_new_tweet(self, save_tweet, document_ids):
        obj = mixer.blend(Reimbursement, search_vector=None, document_id=123456)
        document_ids.return_value = ((42, 123456),)
        with self.settings(**self.credentials):
            Command().handle()
        save_tweet.assert_called_once_with(obj, 42)


class TestMethods(TestCommand):

    def test_get_document_id(self):
        valid = (
            'http://jarbas.serenatadeamor.org/#/documentId/666',
            'http://jarbas.serenatadeamor.org/#/documentId/666/',
            'http://jarbas.serenatadeamor.org/#/documentId/666/something/else',
            'http://jarbas.serenatadeamor.org/#/something/else/documentId/666'
        )
        invalid = (
            'http://jarbas.serenatadeamor.org/#/document/666',
            'http://jarbas.serenatadeamor.org/#/documentid/666/',
            'http://jarbas.serenatadeamor.org/#/year/2015/',
            'http://jarbas.serenatadeamor.org/#/'
        )
        self.assertTrue(all((Command.get_document_id(u) for u in valid)))
        self.assertFalse(any((Command.get_document_id(u) for u in invalid)))

    def test_save_tweet(self):
        status = 9999999999999999999999999
        reimbursement = mixer.blend(Reimbursement, search_vector=None)
        command = Command()
        command.log = MagicMock()
        command.save_tweet(reimbursement, status)
        self.assertEqual(status, reimbursement.tweet.status)
        self.assertEqual(1, command.log.info.call_count)
        self.assertEqual(1, Tweet.objects.count())

    def test_save_duplicated_tweet(self):
        status = 9999999999999999999999999
        reimbursement = mixer.blend(Reimbursement, search_vector=None)
        tweet = mixer.blend(Tweet, status=status, reimbursement=reimbursement)
        command = Command()
        command.log = MagicMock()
        command.save_tweet(reimbursement, status)
        self.assertEqual(status, reimbursement.tweet.status)
        self.assertEqual(1, command.log.info.call_count)
        self.assertEqual(1, Tweet.objects.count())


class TestProperties(TestCommand):

    @patch('jarbas.chamber_of_deputies.management.commands.tweets.twitter.Api')
    def test_tweets_with_clean_database(self, api):
        api.return_value.GetUserTimeline.return_value = range(3)
        with self.settings(**self.credentials):
            command = Command()
        self.assertEqual((0, 1, 2), tuple(command.tweets))
        api.assert_called_once_with(
            '42', '42', '42', '42',
            sleep_on_rate_limit=True
        )
        api.return_value.GetUserTimeline.assert_called_once_with(
            screen_name='RosieDaSerenata',
            count=200,
            include_rts=False,
            exclude_replies=True
        )

    @patch('jarbas.chamber_of_deputies.management.commands.tweets.twitter.Api')
    def test_tweets_with_database(self, api):
        tweet = mixer.blend(
            Tweet,
            reimbursement__search_vector=None,
            status=random_tweet_status()
        )
        api.return_value.GetUserTimeline.return_value = range(3)
        with self.settings(**self.credentials):
            command = Command()
        self.assertEqual((0, 1, 2), tuple(command.tweets))
        api.assert_called_once_with(
            '42', '42', '42', '42',
            sleep_on_rate_limit=True
        )
        api.return_value.GetUserTimeline.assert_called_once_with(
            screen_name='RosieDaSerenata',
            count=200,
            include_rts=False,
            exclude_replies=True,
            since_id=tweet.status
        )

    @patch.object(Command, 'tweets', new_callable=PropertyMock)
    def test_urls(self, tweets):
        tweets.return_value = (
            Status(1234, (Url('http://t.co/12'), Url('http://t.co/34'))),
            Status(42, (Url('http://t.co/42'),))
        )
        expected = (
            (1234, 'http://t.co/12'),
            (1234, 'http://t.co/34'),
            (42, 'http://t.co/42')
        )
        self.assertEqual(expected, tuple(Command().urls))

    @patch.object(Command, 'urls', new_callable=PropertyMock)
    def test_document_ids(self, urls):
        urls.return_value = ((123, 'documentId/1'), (456, 'documentId/2'))
        self.assertEqual(((123, 1), (456, 2)), tuple(Command().document_ids))
