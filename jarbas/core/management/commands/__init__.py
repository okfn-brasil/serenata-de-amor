from datetime import date
from re import match

from django.core.management.base import BaseCommand


class LoadCommand(BaseCommand):

    def add_arguments(self, parser, add_drop_all=True):
        parser.add_argument('dataset', help='Path to the .xz dataset')
        if add_drop_all:
            parser.add_argument(
                '--drop-all', '-d', dest='drop', action='store_true',
                help='Drop all existing records before loading the datasets'
            )

    @staticmethod
    def to_number(value, cast=None):
        if value.lower() in ('nan', ''):
            return None

        number = float(value)
        if cast:
            return cast(number)
        return number

    @staticmethod
    def to_date(text):

        ddmmyyyy = match(r'^[\d]{1,2}/[\d]{1,2}/[\d]{2,4}$', text)
        yyyymmdd = match(r'^[\d]{2,4}-[\d]{1,2}-[\d]{2,4}', text)

        if ddmmyyyy:
            day, month, year = map(int, ddmmyyyy.group().split('/'))
        elif yyyymmdd:
            year, month, day = map(int, yyyymmdd.group().split('-'))
        else:
            return None

        try:
            if 0 <= year <= 50:
                year += 2000
            elif 50 < year <= 99:
                year += 1900
            return date(year, month, day)

        except ValueError:
            return None

    def drop_all(self, model):
        if model.objects.count() != 0:
            msg = 'Deleting all existing records from {} model'
            print(msg.format(self.get_model_name(model)))
            model.objects.all().delete()
            self.print_count(model, permanent=True)

    def print_count(self, model, **kwargs):
        count = kwargs.get('count', model.objects.count())
        raw_msg = 'Current count: {:,} {}s                                    '
        msg = raw_msg.format(count, self.get_model_name(model))
        end = '\n' if kwargs.get('permanent', False) else '\r'
        print(msg, end=end)
        return count

    @staticmethod
    def get_model_name(model):
        return model._meta.label.split('.')[-1]
