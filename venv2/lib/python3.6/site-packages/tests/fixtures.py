from datetime import date, time, timedelta
from decimal import Decimal
import itertools

from django.utils import timezone
from six.moves import xrange

from .models import Person

def get_fixtures(n=None):
    """
      Returns `n` dictionaries of `Person` objects.
      If `n` is not specified it defaults to 6.
    """
    _now = timezone.now().replace(microsecond=0)  # mysql doesn't do microseconds. # NOQA
    _date = date(2015, 3, 28)
    _time = time(13, 0)
    fixtures = [
        {
            'big_age': 59999999999999999, 'comma_separated_age': '1,2,3',
            'age': -99, 'positive_age': 9999, 'positive_small_age': 299,
            'small_age': -299, 'certified': False, 'null_certified': None,
            'name': 'Mike', 'email': 'miketakeahike@mailinator.com',
            'file_path': '/Users/user/fixtures.json', 'slug': 'mike',
            'text': 'here is a dummy text',
            'url': 'https://docs.djangoproject.com',
            'height': Decimal('1.81'), 'date_time': _now,
            'date': _date, 'time': _time, 'float_height': 0.3,
            'remote_addr': '192.0.2.30', 'my_file': 'dummy.txt',
            'image': 'kitten.jpg', 'data': {'name': 'Mike', 'age': -99},
        },
        {
            'big_age': 245999992349999, 'comma_separated_age': '6,2,9',
            'age': 25, 'positive_age': 49999, 'positive_small_age': 315,
            'small_age': 5409, 'certified': False, 'null_certified': True,
            'name': 'Pete', 'email': 'petekweetookniet@mailinator.com',
            'file_path': 'users.json', 'slug': 'pete', 'text': 'dummy',
            'url': 'https://google.com', 'height': Decimal('1.93'),
            'date_time': _now, 'date': _date, 'time': _time,
            'float_height': 0.5, 'remote_addr': '127.0.0.1',
            'my_file': 'fixtures.json',
            'data': [{'name': 'Pete'}, {'name': 'Mike'}],
        },
        {
            'big_age': 9929992349999, 'comma_separated_age': '6,2,9,10,5',
            'age': 29, 'positive_age': 412399, 'positive_small_age': 23315,
            'small_age': -5409, 'certified': False, 'null_certified': True,
            'name': 'Ash', 'email': 'rashash@mailinator.com',
            'file_path': '/Downloads/kitten.jpg', 'slug': 'ash',
            'text': 'bla bla bla', 'url': 'news.ycombinator.com',
            'height': Decimal('1.78'), 'date_time': _now,
            'date': _date, 'time': _time,
            'float_height': 0.8, 'my_file': 'dummy.png',
            'data': {'text': 'bla bla bla', 'names': ['Mike', 'Pete']},
        },
        {
            'big_age': 9992349234, 'comma_separated_age': '12,29,10,5',
            'age': -29, 'positive_age': 4199, 'positive_small_age': 115,
            'small_age': 909, 'certified': True, 'null_certified': False,
            'name': 'Mary', 'email': 'marykrismas@mailinator.com',
            'file_path': 'dummy.png', 'slug': 'mary',
            'text': 'bla bla bla bla bla', 'url': 'news.ycombinator.com',
            'height': Decimal('1.65'), 'date_time': _now,
            'date': _date, 'time': _time, 'float_height': 0,
            'remote_addr': '2a02:42fe::4',
            'data': {'names': {'name': 'Mary'}},
        },
        {
            'big_age': 999234, 'comma_separated_age': '12,1,30,50',
            'age': 1, 'positive_age': 99199, 'positive_small_age': 5,
            'small_age': -909, 'certified': False, 'null_certified': False,
            'name': 'Sandra', 'email': 'sandrasalamandr@mailinator.com',
            'file_path': '/home/dummy.png', 'slug': 'sandra',
            'text': 'this is a dummy text', 'url': 'google.com',
            'height': Decimal('1.59'), 'date_time': _now,
            'date': _date, 'time': _time, 'float_height': 2 ** 2,
            'image': 'dummy.jpeg', 'data': {},
        },
        {
            'big_age': 9999999999, 'comma_separated_age': '1,100,3,5',
            'age': 35, 'positive_age': 1111, 'positive_small_age': 500,
            'small_age': 110, 'certified': True, 'null_certified': None,
            'name': 'Crystal', 'email': 'crystalpalace@mailinator.com',
            'file_path': '/home/dummy.txt', 'slug': 'crystal',
            'text': 'dummy text', 'url': 'docs.djangoproject.com',
            'height': Decimal('1.71'), 'date_time': _now,
            'date': _date, 'time': _time, 'float_height': 2 ** 10,
            'image': 'dummy.png', 'data': [],
        },
    ]
    n = n or len(fixtures)
    fixtures = itertools.cycle(fixtures)
    for _ in xrange(n):
        yield next(fixtures)


def create_fixtures(n=None):
    """
      Wrapper for Person.bulk_create which creates `n` fixtures
    """
    Person.objects.bulk_create(Person(**person)
                               for person in get_fixtures(n))
