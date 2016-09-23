from datetime import timedelta
from http.client import HTTPConnection
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from jarbas.core.models import Document


class Command(BaseCommand):
    help = 'Update the Receipt URL field with valid URLs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', '-d', dest='days', type=int, default=7,
            help='Update URLs older than DAYS days (default: 7)'
        )

    def handle(self, *args, **options):
        print('==> Looking for documents to update')
        limit = now() - timedelta(days=options['days'])
        qs = Document.objects.filter(receipt_url_last_update__lt=limit)
        total = qs.count()
        self.progress = {
            'total': total,
            'count': 0,
            'updated': 0,
            'valid': 0,
            'errors': list()
        }

        print('==> {:,} documents to process'.format(total))
        for url, updated, error in map(update_url, qs.iterator()):
            self.update_progress(url, updated, error)
            print(self.summary(), end='\r')

        print('\r\n')
        print(self.summary())
        if self.progress['errors']:
            print('==> Errors:')
            for count, error in enumerate(progress['errors']):
                print('    {}. {}'.format(count, erro))
        print('==> Done!')

    def update_progress(self, url, updated, error):
        """Update instace's progress according to the return of update_url()"""
        self.progress['count'] += 1

        if updated:
            self.progress['updated'] += 1

        if url:
            self.progress['valid'] +=1

        if error:
            self.progress['errors'].append(error)

        return self.progress

    def summary(self):
        count = self.progress['count']
        done = count / self.progress['total'] * 100
        updated = self.progress['updated'] / self.progress['count'] * 100
        valid = self.progress['valid'] / self.progress['count'] * 100

        msgs = (
            '==> Documents processed: {:,} ({:.1f}%)'.format(count, done),
            'Updated URLs: {:.1f}%'.format(updated),
            'Valid URLs: {:.1f}%'.format(valid)
        )

        return ' • '.join(msgs)


def update_url(document):
    """
    Gets a Document, check if the receipt url is valid and if nedded update the
    Document in the database. Returns a tuple with: (str) the document url (or
    None), (bool) if the document was updated (True means it was), and (str) an
    error (or None).
    """
    scheme, server, path = urlparse(document.get_receipt_url())[:3]

    try:
        http = HTTPConnection(server)
        http.request('HEAD', path)
        status = http.getresponse().status
        error = None
    except TimeoutError:
        status = 408
        error = 'TimeoutError: {}'.format(
            document.get_receipt_url()
        )

    url = document.get_receipt_url() if 200 <= status < 400 else None
    needs_update = document.receipt_url != url

    document.receipt_url_last_update = now()
    if needs_update:
        document.receipt_url = url
    document.save()

    return url, needs_update, error

