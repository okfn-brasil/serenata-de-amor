from datetime import date, time, timedelta
from decimal import Decimal
import random

from django.db.models import F, Func, Value
from django.db.models.functions import Concat
from django.test import TestCase
from django.utils import timezone

from django_bulk_update import helper

from .models import Person, Role, PersonUUID, Brand
from .fixtures import create_fixtures


class BulkUpdateTests(TestCase):

    def setUp(self):
        self.now = timezone.now().replace(microsecond=0)  # mysql doesn't do microseconds. # NOQA
        self.date = date(2015, 3, 28)
        self.time = time(13, 0)
        create_fixtures()

    def _test_field(self, field, idx_to_value_function):
        '''
        Helper to do repeative simple tests on one field.
        '''

        # set
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            value = idx_to_value_function(idx)
            setattr(person, field, value)

        # update
        Person.objects.bulk_update(people, update_fields=[field])

        # check
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            saved_value = getattr(person, field)
            expected_value = idx_to_value_function(idx)
            self.assertEqual(saved_value, expected_value)

    def test_simple_fields(self):
        fn = lambda idx: idx + 27
        for field in ('default', 'big_age', 'age', 'positive_age',
                      'positive_small_age', 'small_age'):
            self._test_field(field,  fn)

    def test_comma_separated_integer_field(self):
        fn = lambda idx: str(idx) + ',27'
        self._test_field('comma_separated_age',  fn)

    def test_boolean_field(self):
        fn = lambda idx: [True, False][idx % 2]
        self._test_field('certified',  fn)

    def test_null_boolean_field(self):
        fn = lambda idx: [True, False, None][idx % 3]
        self._test_field('null_certified',  fn)

    def test_char_field(self):
        NAMES = ['Walter', 'The Dude', 'Donny', 'Jesus', 'Buddha', 'Clark']
        fn = lambda idx: NAMES[idx % 5]
        self._test_field('name',  fn)

    def test_email_field(self):
        EMAILS = ['walter@mailinator.com', 'thedude@mailinator.com',
                  'donny@mailinator.com', 'jesus@mailinator.com',
                  'buddha@mailinator.com', 'clark@mailinator.com']
        fn = lambda idx: EMAILS[idx % 5]
        self._test_field('email',  fn)

    def test_file_path_field(self):
        PATHS = ['/home/dummy.txt', '/Downloads/kitten.jpg',
                 '/Users/user/fixtures.json', 'dummy.png',
                 'users.json', '/home/dummy.png']
        fn = lambda idx: PATHS[idx % 5]
        self._test_field('file_path',  fn)

    def test_slug_field(self):
        SLUGS = ['jesus', 'buddha', 'clark', 'the-dude', 'donny', 'walter']
        fn = lambda idx: SLUGS[idx % 5]
        self._test_field('slug',  fn)

    def test_text_field(self):
        TEXTS = ['this is a dummy text', 'dummy text', 'bla bla bla bla bla',
                 'here is a dummy text', 'dummy', 'bla bla bla']
        fn = lambda idx: TEXTS[idx % 5]
        self._test_field('text',  fn)

    def test_url_field(self):
        URLS = ['docs.djangoproject.com', 'news.ycombinator.com',
                'https://docs.djangoproject.com', 'https://google.com',
                'google.com', 'news.ycombinator.com']
        fn = lambda idx: URLS[idx % 5]
        self._test_field('url',  fn)

    def test_date_time_field(self):
        fn = lambda idx: self.now - timedelta(days=1 + idx, hours=1 + idx)
        self._test_field('date_time',  fn)

    def test_date_field(self):
        fn = lambda idx: self.date - timedelta(days=1 + idx)
        self._test_field('date',  fn)

    def test_time_field(self):
        fn = lambda idx: time(1 + idx, idx)
        self._test_field('time',  fn)

    def test_decimal_field(self):
        fn = lambda idx: Decimal('1.%s' % (50 + idx * 7))
        self._test_field('height',  fn)

    def test_float_field(self):
        fn = lambda idx: float(idx) * 2.0
        self._test_field('float_height',  fn)

    def test_data_field(self):
        fn = lambda idx: {'x': idx}
        self._test_field('data',  fn)

    def test_generic_ipaddress_field(self):
        IPS = ['127.0.0.1', '192.0.2.30', '2a02:42fe::4', '10.0.0.1',
               '8.8.8.8']
        fn = lambda idx: IPS[idx % 5]
        self._test_field('remote_addr',  fn)

    def test_image_field(self):
        IMGS = ['kitten.jpg', 'dummy.png', 'user.json', 'dummy.png', 'foo.gif']
        fn = lambda idx: IMGS[idx % 5]

        self._test_field('image',  fn)
        self._test_field('my_file',  fn)

    def test_custom_fields(self):
        values = {}
        people = Person.objects.all()
        people_dict = {p.name: p for p in people}
        person = people_dict['Mike']
        person.data = {'name': 'mikey', 'age': 99, 'ex': -99}
        values[person.pk] = {'name': 'mikey', 'age': 99, 'ex': -99}

        person = people_dict['Mary']
        person.data = {'names': {'name': []}}
        values[person.pk] = {'names': {'name': []}}

        person = people_dict['Pete']
        person.data = []
        values[person.pk] = []

        person = people_dict['Sandra']
        person.data = [{'name': 'Pete'}, {'name': 'Mike'}]
        values[person.pk] = [{'name': 'Pete'}, {'name': 'Mike'}]

        person = people_dict['Ash']
        person.data = {'text': 'bla'}
        values[person.pk] = {'text': 'bla'}

        person = people_dict['Crystal']
        values[person.pk] = person.data

        Person.objects.bulk_update(people)

        people = Person.objects.all()
        for person in people:
            self.assertEqual(person.data, values[person.pk])

    def test_update_fields(self):
        """
            Only the fields in "update_fields" are updated
        """
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age += 1
            person.height += Decimal('0.01')
        Person.objects.bulk_update(people, update_fields=['age'])

        people2 = Person.objects.order_by('pk').all()
        for person1, person2 in zip(people, people2):
            self.assertEqual(person1.age, person2.age)
            self.assertNotEqual(person1.height, person2.height)

    def test_update_foreign_key_fields(self):
        roles = [Role.objects.create(code=1), Role.objects.create(code=2)]
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age += 1
            person.height += Decimal('0.01')
            person.role = roles[0] if idx % 2 == 0 else roles[1]
        Person.objects.bulk_update(people)

        people2 = Person.objects.order_by('pk').all()
        for person1, person2 in zip(people, people2):
            self.assertEqual(person1.role.code, person2.role.code)
            self.assertEqual(person1.age, person2.age)
            self.assertEqual(person1.height, person2.height)

    def test_update_foreign_key_fields_explicit(self):
        roles = [Role.objects.create(code=1), Role.objects.create(code=2)]
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age += 1
            person.height += Decimal('0.01')
            person.role = roles[0] if idx % 2 == 0 else roles[1]
            person.big_age += 40
        Person.objects.bulk_update(people,
                                   update_fields=['age', 'height', 'role'])

        people2 = Person.objects.order_by('pk').all()
        for person1, person2 in zip(people, people2):
            self.assertEqual(person1.role.code, person2.role.code)
            self.assertEqual(person1.age, person2.age)
            self.assertEqual(person1.height, person2.height)
            self.assertNotEqual(person1.big_age, person2.big_age)

    def test_update_foreign_key_fields_explicit_with_id_suffix(self):
        roles = [Role.objects.create(code=1), Role.objects.create(code=2)]
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age += 1
            person.height += Decimal('0.01')
            person.role = roles[0] if idx % 2 == 0 else roles[1]
        Person.objects.bulk_update(people,
                                   update_fields=['age', 'height', 'role_id'])

        people2 = Person.objects.order_by('pk').all()
        for person1, person2 in zip(people, people2):
            self.assertEqual(person1.role.code, person2.role.code)
            self.assertEqual(person1.age, person2.age)
            self.assertEqual(person1.height, person2.height)

    def test_update_foreign_key_exclude_fields_explicit(self):
        roles = [Role.objects.create(code=1), Role.objects.create(code=2)]
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age += 1
            person.height += Decimal('0.01')
            person.role = roles[0] if idx % 2 == 0 else roles[1]
            person.big_age += 40
        Person.objects.bulk_update(people,
                                   update_fields=['age', 'height'],
                                   exclude_fields=['role'])

        people2 = Person.objects.order_by('pk').all()
        for person1, person2 in zip(people, people2):
            self.assertTrue(isinstance(person1.role, Role))
            self.assertEqual(person2.role, None)
            self.assertEqual(person1.age, person2.age)
            self.assertEqual(person1.height, person2.height)
            self.assertNotEqual(person1.big_age, person2.big_age)

    def test_update_foreign_key_exclude_fields_explicit_with_id_suffix(self):
        roles = [Role.objects.create(code=1), Role.objects.create(code=2)]
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age += 1
            person.height += Decimal('0.01')
            person.role = roles[0] if idx % 2 == 0 else roles[1]
        Person.objects.bulk_update(people,
                                   update_fields=['age', 'height'],
                                   exclude_fields=['role_id'])

        people2 = Person.objects.order_by('pk').all()
        for person1, person2 in zip(people, people2):
            self.assertTrue(isinstance(person1.role, Role))
            self.assertEqual(person2.role, None)
            self.assertEqual(person1.age, person2.age)
            self.assertEqual(person1.height, person2.height)

    def test_exclude_fields(self):
        """
            Only the fields not in "exclude_fields" are updated
        """
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age += 1
            person.height += Decimal('0.01')
        Person.objects.bulk_update(people, exclude_fields=['age'])

        people2 = Person.objects.order_by('pk').all()
        for person1, person2 in zip(people, people2):
            self.assertNotEqual(person1.age, person2.age)
            self.assertEqual(person1.height, person2.height)

    def test_exclude_fields_with_tuple_exclude_fields(self):
        """
            Only the fields not in "exclude_fields" are updated
        """
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age += 1
            person.height += Decimal('0.01')
        Person.objects.bulk_update(people, exclude_fields=('age',))

        people2 = Person.objects.order_by('pk').all()
        for person1, person2 in zip(people, people2):
            self.assertNotEqual(person1.age, person2.age)
            self.assertEqual(person1.height, person2.height)

    def test_object_list(self):
        """
          Pass in a list instead of a queryset for bulk updating
        """
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.big_age = idx + 27
        Person.objects.bulk_update(list(people))

        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            self.assertEqual(person.big_age, idx + 27)

    def test_empty_list(self):
        """
        Update no elements, passed as a list
        """
        Person.objects.bulk_update([])

    def test_empty_queryset(self):
        """
        Update no elements, passed as a queryset
        """
        people = Person.objects.filter(name="Aceldotanrilsteucsebces ECSbd")
        Person.objects.bulk_update(people)

    def test_one_sized_list(self):
        """
        Update one sized list, check if have a syntax error
        for some db backends.
        """
        people = Person.objects.all()[:1]
        Person.objects.bulk_update(list(people))

    def test_one_sized_queryset(self):
        """
        Update one sized list, check if have a syntax error
        for some db backends.
        """
        people = Person.objects.filter(name='Mike')
        Person.objects.bulk_update(people)

    def test_wrong_field_names(self):
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.big_age = idx + 27
        self.assertRaises(TypeError, Person.objects.bulk_update,
                          people, update_fields=['somecolumn', 'name'])

        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.big_age = idx + 27
        self.assertRaises(TypeError, Person.objects.bulk_update,
                          people, exclude_fields=['somecolumn'])

        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.big_age = idx + 27
        self.assertRaises(TypeError, Person.objects.bulk_update,
                          people, update_fields=['somecolumn'],
                          exclude_fields=['someothercolumn'])

    def test_batch_size(self):
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age += 1
            person.height += Decimal('0.01')
        updated_obj_count = Person.objects.bulk_update(people, batch_size=1)
        self.assertEqual(updated_obj_count, len(people))

        people2 = Person.objects.order_by('pk').all()
        for person1, person2 in zip(people, people2):
            self.assertEqual(person1.age, person2.age)
            self.assertEqual(person1.height, person2.height)

    def test_array_field(self):
        """
        Test to 'bulk_update' a postgresql's ArrayField.
        """
        Brand.objects.bulk_create([
            Brand(name='b1', codes=['a', 'b']),
            Brand(name='b2', codes=['x']),
            Brand(name='b3', codes=['x', 'y', 'z']),
            Brand(name='b4', codes=['1', '2']),
        ])

        brands = Brand.objects.all()

        for brand in brands:
            brand.codes.append(brand.codes[0]*2)

        Brand.objects.bulk_update(brands)

        expected = ['aa', 'xx', 'xx', '11']
        for value, brand in zip(expected, brands):
            self.assertEqual(brand.codes[-1], value)

    def test_uuid_pk(self):
        """
        Test 'bulk_update' with a model whose pk is an uuid.
        """
        # create
        PersonUUID.objects.bulk_create(
            [PersonUUID(age=c) for c in range(20, 30)])

        # set
        people = PersonUUID.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age = idx * 11

        # update
        PersonUUID.objects.bulk_update(people, update_fields=['age'])

        # check
        people = PersonUUID.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            saved_value = person.age
            expected_value = idx * 11
            self.assertEqual(saved_value, expected_value)

    def test_F_expresion(self):

        # initialize
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age = idx*10
            person.save()

        # set
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            person.age = F('age') - idx

        # update
        Person.objects.bulk_update(people)

        # check
        people = Person.objects.order_by('pk').all()
        for idx, person in enumerate(people):
            saved_value = person.age
            expected_value = idx*10 - idx
            self.assertEqual(saved_value, expected_value)

    def test_Func_expresion(self):

        # initialize
        ini_values = 'aA', 'BB', '', 'cc', '12'
        people = Person.objects.order_by('pk').all()
        for value, person in zip(ini_values, people):
            person.name = value
            person.text = value*2
            person.save()

        # set
        people = Person.objects.order_by('pk').all()
        for person in people:
            person.name = Func(F('name'), function='UPPER')
            person.text = Func(F('text'), function='LOWER')

        # update
        Person.objects.bulk_update(people)

        # check
        people = Person.objects.order_by('pk').all()

        expected_values = 'AA', 'BB', '', 'CC', '12'
        for expected_value, person in zip(expected_values, people):
            saved_value = person.name
            self.assertEqual(saved_value, expected_value)

        expected_values = 'aaaa', 'bbbb', '', 'cccc', '1212'
        for expected_value, person in zip(expected_values, people):
            saved_value = person.text
            self.assertEqual(saved_value, expected_value)

    def test_Concat_expresion(self):

        # initialize
        ini_values_1 = 'a', 'b', 'c', 'd', 'e'
        ini_values_2 = 'v', 'w', 'x', 'y', 'z'

        people = Person.objects.order_by('pk').all()
        for value1, value2, person in zip(ini_values_1, ini_values_2, people):
            person.slug = value1
            person.name = value2
            person.save()

        # set
        people = Person.objects.order_by('pk').all()
        for person in people:
            person.text = Concat(F('slug'), Value('@'), F('name'), Value('|'))

        # update
        Person.objects.bulk_update(people)

        # check
        people = Person.objects.order_by('pk').all()

        expected_values = 'a@v|', 'b@w|', 'c@x|', 'd@y|', 'e@z|'
        for expected_value, person in zip(expected_values, people):
            saved_value = person.text
            self.assertEqual(saved_value, expected_value)

    def test_different_deferred_fields(self):

        # initialize
        people = Person.objects.order_by('pk').all()
        for person in people:
            person.name = 'original name'
            person.text = 'original text'
            person.save()

        # set
        people1 = list(Person.objects.filter(age__lt=10).only('name'))
        people2 = list(Person.objects.filter(age__gte=10).only('text'))
        people = people1 + people2
        for person in people:
            if person.age < 10:
                person.name = 'changed name'
            else:
                person.text = 'changed text'

        # update
        count = Person.objects.bulk_update(people)

        # check
        people = Person.objects.order_by('pk').all()
        self.assertEquals(count, people.count())
        for person in people:
            if person.age < 10:
                self.assertEquals(person.name, 'changed name')
                self.assertEquals(person.text, 'original text')
            else:
                self.assertEquals(person.name, 'original name')
                self.assertEquals(person.text, 'changed text')

    def test_different_deferred_fields_02(self):

        # initialize
        people = Person.objects.order_by('pk').all()
        for person in people:
            person.name = 'original name'
            person.text = 'original text'
            person.save()

        # set
        people1 = list(Person.objects.filter(age__lt=10).only('name'))
        people2 = list(Person.objects.filter(age__gte=10).only('text'))
        people = people1 + people2
        for person in people:
            if person.age < 10:
                person.name = 'changed name'
            else:
                person.text = 'changed text'

        # update
        count = Person.objects.bulk_update(people, exclude_fields=['name'])

        # check
        people = Person.objects.order_by('pk').all()
        self.assertEquals(count, people.count())
        for person in people:
            if person.age < 10:
                self.assertEquals(person.name, 'original name')
                self.assertEquals(person.text, 'original text')
            else:
                self.assertEquals(person.name, 'original name')
                self.assertEquals(person.text, 'changed text')


class NumQueriesTest(TestCase):

    def setUp(self):
        create_fixtures(5)

    def test_num_queries(self):
        """
        Queries:
            - retrieve objects
            - update objects
        """
        people = Person.objects.order_by('pk').all()
        self.assertNumQueries(2, Person.objects.bulk_update, people)

    def test_already_evaluated_queryset(self):
        """
        Queries:
            - update objects

        (objects are already retrieved, because of the previous loop)
        """
        people = Person.objects.all()
        for person in people:
            person.age += 2
            person.name = Func(F('name'), function='UPPER')
            person.text = 'doc'
            person.height -= Decimal(0.5)
        self.assertNumQueries(1, Person.objects.bulk_update, people)

    def test_explicit_fields(self):
        """
        Queries:
            - retrieve objects
            - update objects
        """
        people = Person.objects.all()
        self.assertNumQueries(
            2, Person.objects.bulk_update, people,
            update_fields=['date', 'time', 'image', 'slug', 'height'],
            exclude_fields=['date', 'url']
        )

    def test_deferred_fields(self):
        """
        Queries:
            - retrieve objects
            - update objects
        """
        people = Person.objects.all().only('date', 'url', 'age', 'image')
        self.assertNumQueries(2, Person.objects.bulk_update, people)

    def test_different_deferred_fields(self):
        """
        Queries:
            - retrieve objects
            - update objects
        """
        all_people = Person.objects
        people1 = all_people.filter(age__lt=10).defer('date', 'url', 'age')
        people2 = all_people.filter(age__gte=10).defer('url', 'name', 'big_age')
        people = people1 | people2
        self.assertNumQueries(2, Person.objects.bulk_update, people)

    def test_deferred_fields_and_excluded_fields(self):
        """
        Queries:
            - retrieve objects
            - update objects
        """
        people = Person.objects.all().only('date', 'age', 'time', 'image', 'slug')
        self.assertNumQueries(2, Person.objects.bulk_update, people,
                              exclude_fields=['date', 'url'])

    def test_list_of_objects(self):
        """
        Queries:
            - update objects

        (objects are already retrieved, because of the cast to list)
        """
        people = list(Person.objects.all())
        self.assertNumQueries(1, Person.objects.bulk_update, people)

    def test_fields_to_update_are_deferred(self):
        """
        As all fields in 'update_fields' are deferred,
        a query will be done for each obj and field to retrieve its value.
        """
        people = Person.objects.all().only('pk')
        update_fields = ['date', 'time', 'image']
        expected_queries = len(update_fields) * Person.objects.count() + 2
        self.assertNumQueries(expected_queries, Person.objects.bulk_update,
                              people, update_fields=update_fields)

    def test_no_field_to_update(self):
        """
        Queries:
            - retrieve objects

        (as update_fields is empty, no update query will be done)
        """
        people = Person.objects.all()
        self.assertNumQueries(1, Person.objects.bulk_update,
                              people, update_fields=[])

    def test_no_objects(self):
        """
        Queries:
            - retrieve objects

        (as no objects is actually retrieved, no update query will be done)
        """
        people = Person.objects.filter(name='xxx')
        self.assertNumQueries(1, Person.objects.bulk_update,
                              people, update_fields=['age', 'height'])

    def test_batch_size(self):
        """
        Queries:
            - retrieve objects
            - update objects * 3
        """
        self.assertEquals(Person.objects.count(), 5)
        people = Person.objects.order_by('pk').all()
        self.assertNumQueries(4, Person.objects.bulk_update,
                              people, batch_size=2)


class GetFieldsTests(TestCase):

    total_fields = 25

    def setUp(self):
        create_fixtures()

    def _assertEquals(self, fields, names):
        self.assertEquals(
            set(field.name for field in fields),
            set(names),
        )

    def _assertIn(self, names, fields):
        field_names = [field.name for field in fields]
        for name in names:
            self.assertIn(name, field_names)

    def _assertNotIn(self, names, fields):
        field_names = [field.name for field in fields]
        for name in names:
            self.assertNotIn(name, field_names)

    def test_get_all_fields(self):
        meta = Person.objects.first()._meta
        update_fields = None
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self.assertEquals(len(fields), self.total_fields)

    def test_dont_get_primary_key(self):
        meta = Person.objects.first()._meta
        update_fields = None
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self._assertIn(['id'], meta.get_fields())  # sanity check
        self._assertNotIn(['id'], fields)  # actual test

        meta = PersonUUID.objects.create(age=3)._meta
        update_fields = None
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self._assertIn(['uuid'], meta.get_fields())  # sanity check
        self._assertNotIn(['uuid'], fields)  # actual test

    def test_dont_get_reversed_relations(self):
        meta = Person.objects.first()._meta
        update_fields = None
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self._assertIn(['companies'], meta.get_fields())  # sanity check
        self._assertNotIn(['companies'], fields)  # actual test

    def test_dont_get_many_to_many_relations(self):
        meta = Person.objects.first()._meta
        update_fields = None
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self._assertIn(['jobs'], meta.get_fields())  # sanity check
        self._assertNotIn(['jobs'], fields)  # actual test

    def test_update_fields(self):
        meta = Person.objects.first()._meta
        update_fields = ['age', 'email', 'text']
        exclude_fields = []
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self._assertEquals(fields, ['age', 'email', 'text'])

    def test_update_fields_and_exclude_fields(self):
        meta = Person.objects.first()._meta
        update_fields = ['age', 'email', 'text']
        exclude_fields = ['email', 'height']
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self._assertEquals(fields, ['age', 'text'])

    def test_empty_update_fields(self):
        meta = Person.objects.first()._meta
        update_fields = []
        exclude_fields = ['email', 'height']
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self._assertEquals(fields, [])

    def test_exclude_a_foreignkey(self):
        meta = Person.objects.first()._meta
        update_fields = None
        exclude_fields = ['email', 'role']
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self.assertEquals(len(fields), self.total_fields - 2)
        self._assertNotIn(['email', 'role'], fields)

    def test_exclude_foreignkey_with_id_suffix(self):
        meta = Person.objects.first()._meta
        update_fields = None
        exclude_fields = ['email', 'role_id']
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self.assertEquals(len(fields), self.total_fields - 2)
        self._assertNotIn(['email', 'role'], fields)

    def test_get_a_foreignkey(self):
        meta = Person.objects.first()._meta
        update_fields = ['role', 'my_file']
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self._assertEquals(fields, ['role', 'my_file'])

    def test_get_foreignkey_with_id_suffix(self):
        meta = Person.objects.first()._meta
        update_fields = ['role_id', 'my_file']
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self._assertEquals(fields, ['role', 'my_file'])

    def test_obj_argument(self):
        obj = Person.objects.first()
        meta = obj._meta
        update_fields = None
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta, obj)
        self.assertEquals(len(fields), self.total_fields)

    def test_only_get_not_deferred_fields(self):
        obj = Person.objects.only('name', 'age', 'height').first()
        meta = obj._meta
        update_fields = None
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta, obj)
        self._assertEquals(fields, ['name', 'age', 'height'])

    def test_only_and_exclude_fields(self):
        obj = Person.objects.only('name', 'age', 'height').first()
        meta = obj._meta
        update_fields = None
        exclude_fields = ['age', 'date']
        fields = helper.get_fields(update_fields, exclude_fields, meta, obj)
        self._assertEquals(fields, ['name', 'height'])

    def test_only_and_exclude_fields_02(self):
        obj = Person.objects.defer('age', 'height').first()
        meta = obj._meta
        update_fields = None
        exclude_fields = ['image', 'data']
        fields = helper.get_fields(update_fields, exclude_fields, meta, obj)
        self.assertEquals(len(fields), self.total_fields - 4)
        self._assertNotIn(['age', 'height', 'image', 'data'], fields)

    def test_update_fields_over_not_deferred_field(self):
        obj = Person.objects.only('name', 'age', 'height').first()
        meta = obj._meta
        update_fields = ['date', 'time', 'age']
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta, obj)
        self._assertEquals(fields, ['date', 'time', 'age'])

    def test_update_fields_over_not_deferred_field_02(self):
        obj = Person.objects.only('name', 'age', 'height').first()
        meta = obj._meta
        update_fields = []
        exclude_fields = None
        fields = helper.get_fields(update_fields, exclude_fields, meta, obj)
        self._assertEquals(fields, [])

    def test_arguments_as_tuples(self):
        meta = Person.objects.first()._meta
        update_fields = ('age', 'email', 'text')
        exclude_fields = ('email', 'height')
        fields = helper.get_fields(update_fields, exclude_fields, meta)
        self._assertEquals(fields, ['age', 'text'])

    def test_validate_fields(self):
        meta = Person.objects.first()._meta

        update_fields = ['age', 'wrong_name', 'text']
        exclude_fields = ('email', 'height')
        self.assertRaises(TypeError, helper.get_fields,
                          update_fields, exclude_fields, meta)

        update_fields = ('age', 'email', 'text')
        exclude_fields = ('email', 'bad_name')
        self.assertRaises(TypeError, helper.get_fields,
                          update_fields, exclude_fields, meta)

        update_fields = ('companies', )
        exclude_fields = None
        self.assertRaises(TypeError, helper.get_fields,
                          update_fields, exclude_fields, meta)

        update_fields = None
        exclude_fields = ['jobs']
        self.assertRaises(TypeError, helper.get_fields,
                          update_fields, exclude_fields, meta)
