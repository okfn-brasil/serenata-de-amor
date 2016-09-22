from http.client import HTTPConnection
from urllib.parse import urlparse

from django.core.management.base import BaseCommand

from jarbas.core.models import Document


class Command(BaseCommand):
    help = 'Update the Receipt URL field with valid URLs'

    def handle(self, *args, **options):
        progress = {
            'total': Document.objects.count(),
            'count': 0,
            'updated': 0,
            'valid': 0,
            'errors': list()
        }
        update_list = list()

        fields = ('pk', 'applicant_id', 'year', 'document_id')
        documents = Document.objects.only(*fields).iterator()

        for url, updated, error in map(self.update_url, documents):
            progress['count'] += 1

            if updated:
                progress['updated'] += 1

            if url:
                progress['valid'] +=1

            if error:
                progress['errors'].append(error)

            print(self.summary(**progress), end='\r')


        print('\r\n')
        print(self.summary(**progress))
        print('==> Errors:')
        for count, error in enumerate(progress['errors']):
            print('    {}. {}'.format(count, erro))

    @staticmethod
    def update_url(document):
        """
        Get a Document, check if the receipt url is valid and if nedded update
        the Document in the database. Returns a tuple with the url (str or
        None), and a boolean (True if it was updated, False otherwise).
        """
        scheme, server, path = urlparse(document.get_receipt_url())[:3]

        try:
            http = HTTPConnection(server)
            http.request('HEAD', path)
            status = http.getresponse().status
            error = None
        except TimeoutError:
            status = 408
            error = 'TimeoutError: [pk={}] {}'.format(
                document.pk,
                document.get_receipt_url()
            )

        url = document.get_receipt_url() if 200 <= status < 400 else None
        needs_update = document.receipt_url != url

        if needs_update:
            document.receipt_url = url
            document.save()

        return url, needs_update, error

    @staticmethod
    def summary(**kwargs):
        total = kwargs.get('total', 0)
        count = kwargs.get('count', 0)
        updated = kwargs.get('updated', 0)
        valid = kwargs.get('valid', 0)

        done = count / total * 100
        updated = updated / count * 100
        valid = valid / count * 100

        msgs = (
            '==> Documents processed: {:,} ({:.1f}%)'.format(count, done),
            'Updated URLs: {:.1f}%'.format(updated * 100),
            'Valid URLs: {:.1f}%'.format(valid * 100)
        )

        return ' • '.join(msgs)
