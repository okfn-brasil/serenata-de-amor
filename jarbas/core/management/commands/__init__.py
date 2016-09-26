import os
from tempfile import NamedTemporaryFile
from urllib.request import urlretrieve

from django.core.management.base import BaseCommand
from django.conf import settings


class LoadCommand(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--source', '-s', dest='source', default=None,
            help='Data directory of Serenata de Amor (dataset source)'
        )
        parser.add_argument(
            '--drop-all', '-d', dest='drop', action='store_true',
            help='Drop all existing records before loading the datasets'
        )

    def load_remote(self, name):
        """Load a document from Amazon S3"""
        url = self.get_url(name)
        print("Loading " + url)
        with NamedTemporaryFile(delete=False) as tmp:
            urlretrieve(url, filename=tmp.name)
            return tmp.name

    def load_local(self, source, name):
        """Load documents from local source"""
        path = self.get_path(source, name)

        if not os.path.exists(path):
            print(path + " not found")
            return None

        print("Loading " + path)
        return path

    def get_url(self, suffix):
        return 'https://{region}.amazonaws.com/{bucket}/{file_name}'.format(
            region=settings.AMAZON_S3_REGION,
            bucket=settings.AMAZON_S3_BUCKET,
            file_name=self.get_file_name(suffix)
        )

    def get_path(self, source, name):
        return os.path.join(source, self.get_file_name(name))

    @staticmethod
    def get_file_name(name):
        return '{date}-{name}.xz'.format(
            date=settings.AMAZON_S3_DATASET_DATE,
            name=name
        )

    def drop_all(self, model):
        if model.objects.count() != 0:
            msg = 'Deleting all existing records from {} model'
            print(msg.format(self.get_model_name(model)))
            model.objects.all().delete()
            self.print_count(model, permanent=True)

    def print_count(self, model, **kwargs):
        raw_msg = 'Current count: {:,} {}s                                    '
        msg = raw_msg.format(model.objects.count(), self.get_model_name(model))
        end = '\n' if kwargs.get('permanent', False) else '\r'
        print(msg, end=end)

    @staticmethod
    def get_model_name(model):
        return model._meta.label.split('.')[-1]
