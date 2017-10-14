from django.test import TestCase
from mixer.backend.django import mixer

from jarbas.chamber_of_deputies.models import Tweet


class TestTweet(TestCase):

    def setUp(self):
        self.tweet = mixer.blend(Tweet, reimbursement__search_vector=None, status=42)

    def test_ordering(self):
        mixer.blend(Tweet, reimbursement__search_vector=None, status=1)
        self.assertEqual(42, Tweet.objects.first().status)

    def test_get_url(self):
        expected = 'https://twitter.com/RosieDaSerenata/status/42'
        self.assertEqual(expected, self.tweet.get_url())

    def test_repr(self):
        expected = '<Tweet: status=42>'
        self.assertEqual(expected, self.tweet.__repr__())

    def test_str(self):
        self.assertEqual(self.tweet.get_url(), str(self.tweet))
