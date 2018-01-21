""" Mixer factories. """

import datetime
import decimal
import inspect

from . import _compat as _, mix_types as t
from ._faker import faker


class GenFactoryMeta(type):

    """ Precache generators. """

    def __new__(mcs, name, bases, params):
        generators = dict()
        fakers = dict()
        types = dict()

        for cls in bases:
            if isinstance(cls, GenFactoryMeta):
                generators.update(cls.generators)
                fakers.update(cls.fakers)
                types.update(cls.types)

        fakers.update(params.get('fakers', dict()))
        types.update(params.get('types', dict()))

        types = dict(mcs.__flat_keys(types))

        if types:
            for atype, btype in types.items():
                factory = generators.get(btype)
                if factory:
                    generators[atype] = factory

        generators.update(params.get('generators', dict()))
        generators = dict(mcs.__flat_keys(generators))

        params['generators'] = generators
        params['fakers'] = fakers
        params['types'] = types

        return super(GenFactoryMeta, mcs).__new__(mcs, name, bases, params)

    @staticmethod
    def __flat_keys(d):
        for key, value in d.items():
            if isinstance(key, (tuple, list)):
                for k in key:
                    yield k, value
                continue
            yield key, value


class GenFactory(_.with_metaclass(GenFactoryMeta)):

    """ Make generators for types. """

    generators = {
        bool: faker.pybool,
        float: faker.pyfloat,
        int: faker.random_int,
        str: faker.pystr,
        bytes: faker.pybytes,
        list: faker.pylist,
        set: faker.pyset,
        tuple: faker.pytuple,
        dict: faker.pydict,
        datetime.date: faker.date,
        datetime.datetime: faker.date_time,
        datetime.time: faker.time,
        decimal.Decimal: faker.pydecimal,
        t.BigInteger: faker.big_integer,
        t.EmailString: faker.email,
        t.HostnameString: faker.domain_name,
        t.IP4String: faker.ipv4,
        t.IP6String: faker.ipv6,
        t.IPString: faker.ip_generic,
        t.NullOrBoolean: faker.null_boolean,
        t.PositiveDecimal: faker.positive_decimal,
        t.PositiveInteger: faker.positive_integer,
        t.PositiveSmallInteger: faker.small_positive_integer,
        t.SmallInteger: faker.small_integer,
        t.Text: faker.text,
        t.URL: faker.url,
        t.UUID: faker.uuid,
        type(None): '',
    }

    fakers = {
        ('address', str): faker.street_address,
        ('body', str): faker.text,
        ('category', str): faker.genre,
        ('city', str): faker.city,
        ('company', str): faker.company,
        ('content', str): faker.text,
        ('country', str): faker.country,
        ('description', str): faker.text,
        ('domain', str): faker.domain_name,
        ('email', str): faker.email,
        ('first_name', str): faker.first_name,
        ('firstname', str): faker.first_name,
        ('genre', str): faker.genre,
        ('last_name', str): faker.last_name,
        ('lastname', str): faker.last_name,
        ('lat', float): faker.latitude,
        ('latitude', float): faker.latitude,
        ('login', str): faker.user_name,
        ('lon', float): faker.longitude,
        ('longitude', float): faker.longitude,
        ('name', str): faker.name,
        ('percent', decimal.Decimal): faker.percent_decimal,
        ('percent', int): faker.percent,
        ('phone', str): faker.phone_number,
        ('site', str): faker.url,
        ('slug', str): faker.slug,
        ('street', str): faker.street_name,
        ('time_zone', str): faker.timezone,
        ('timezone', str): faker.timezone,
        ('title', str): faker.title,
        ('url', t.URL): faker.uri,
        ('url', str): faker.uri,
        ('username', str): faker.user_name,
    }

    types = {
        _.string_types: str,
        _.integer_types: int,
    }

    @classmethod
    def cls_to_simple(cls, fcls):
        """ Translate class to one of simple base types.

        :return type: A simple type for generation

        """
        if fcls in cls.types:
            return cls.types[fcls]

        if fcls in cls.generators:
            return fcls

        if inspect.isclass(fcls):
            for stype in cls.types:
                if issubclass(fcls, stype):
                    return cls.types[stype]

        return None

    @staticmethod
    def name_to_simple(fname):
        """ Translate name to one of simple base names.

        :return str:

        """
        fname = fname or ''
        return fname.lower().strip()

    @classmethod
    def get_fabric(cls, fcls, fname=None, fake=False):
        """ Make a objects fabric  based on class and name.

        :return function:

        """
        simple = cls.cls_to_simple(fcls)
        func = cls.generators.get(fcls) or cls.generators.get(simple)

        if not func and fcls.__bases__:
            func = cls.generators.get(fcls.__bases__[0])

        if fname and fake and (fname, simple) in cls.fakers:
            fname = cls.name_to_simple(fname)
            func = cls.fakers.get((fname, simple)) or func

        if func is None:
            return False

        return func
