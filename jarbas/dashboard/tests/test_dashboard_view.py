from itertools import chain

from django.shortcuts import resolve_url
from django.test import TestCase
from mixer.backend.django import mixer

from jarbas.chamber_of_deputies.models import Reimbursement


class TestDashboard(TestCase):

    def setUp(self):
        obj = mixer.blend(Reimbursement, search_vector=None)
        self.urls = (
            resolve_url('dashboard:index'),
            resolve_url('dashboard:chamber_of_deputies_reimbursement_changelist'),
            resolve_url('dashboard:chamber_of_deputies_reimbursement_change', obj.pk),
            resolve_url('dashboard:chamber_of_deputies_reimbursement_history', obj.pk),
        )
        self.forbidden = (
            '/login/',
            '/logout/',
            '/password_change/',
            '/password_change/done/',
            '/auth/group/,',
            '/auth/user/,',
            '/auth/'
        )


class TestGet(TestDashboard):

    def test_successful_get(self):
        for url in self.urls:
            resp = self.client.get(url)
            self.assertEqual(200, resp.status_code, url)

    def test_forbidden_get(self):
        for url in self.forbidden:
            resp = self.client.get(url)
            self.assertEqual(404, resp.status_code, url)


class TestPostPutDelete(TestDashboard):

    def get_responses(self, url):
        methods = ('post', 'put', 'patch', 'delete', 'head')
        for method in methods:
            reference = '{} {}'.format(method.upper(), url)
            request = getattr(self.client, method)
            yield request(url, follow=False), reference

    def test_forbidden_methods(self):
        responses = map(self.get_responses, self.urls)
        for resp, reference in chain(*responses):
            self.assertEqual(403, resp.status_code, reference)

    def test_forbidden_urls(self):
        responses = map(self.get_responses, self.forbidden)
        for resp, reference in chain(*responses):
            self.assertEqual(404, resp.status_code, reference)
