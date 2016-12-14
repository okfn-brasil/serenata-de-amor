import csv
import lzma

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from jarbas.core.management.commands import LoadCommand
from jarbas.core.models import Activity, Supplier


class Command(LoadCommand):
    help = 'Load Serenata de Amor supplier dataset into the database'

    def handle(self, *args, **options):
        self.date = options.get('dataset_version')
        self.source = options.get('source')
        self.count = self.print_count(Supplier)
        print('self.cont =', self.count)
        print('Starting with {:,} suppliers'.format(self.count))

        if options.get('drop', False):
            self.drop_all(Supplier)
            self.drop_all(Activity)
            self.count = 0

        self.save_suppliers(self.get_dataset('companies'))

    def save_suppliers(self, dataset):
        """
        Receives path to the dataset file and create a Supplier object for
        each row of each file. It creates the related activity when needed.
        """
        skip = ('main_activity', 'secondary_activty')
        keys = list(f.name for f in Supplier._meta.fields if f not in skip)
        with lzma.open(dataset, mode='rt') as file_handler:
            for row in csv.DictReader(file_handler):
                main, secondary = self.save_activities(row)

                filtered = {k: v for k, v in row.items() if k in keys}
                obj = Supplier.objects.create(**self.serialize(filtered))
                for activity in main:
                    obj.main_activity.add(activity)
                for activity in secondary:
                    obj.secondary_activity.add(activity)
                obj.save()

                self.count += 1
                self.print_count(Supplier, count=self.count)

    def save_activities(self, row):
        data = dict(
            code=row['main_activity_code'],
            description=row['main_activity']
        )
        main = Activity.objects.update_or_create(**data, defaults=data)[0]

        secondaries = list()
        for num in range(1, 100):
            code = row.get('secondary_activity_{}_code'.format(num))
            description = row.get('secondary_activity_{}'.format(num))
            if code and description:
                d = dict(code=code, description=description)
                obj = Activity.objects.update_or_create(**d, defaults=d)[0]
                secondaries.append(obj)

        return [main], secondaries

    def serialize(self, row):
        row['email'] = self.to_email(row['email'])

        dates = ('opening', 'situation_date', 'special_situation_date')
        for key in dates:
            row[key] = self.to_date(row[key])

        decimals = ('latitude', 'longitude')
        for key in decimals:
            row[key] = self.to_number(row[key])

        return row

    @staticmethod
    def to_email(email):
        try:
            validate_email(email)
            return email

        except ValidationError:
            return None
