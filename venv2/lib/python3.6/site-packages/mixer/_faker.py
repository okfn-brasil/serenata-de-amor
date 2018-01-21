""" Integrate Faker to the Mixer. """
import decimal as dc
import locale as pylocale
from collections import defaultdict

from faker import Factory, Generator
from faker.config import DEFAULT_LOCALE, AVAILABLE_LOCALES, PROVIDERS
from faker.providers import BaseProvider

SMALLINT = 32768  # Safe in most databases according to Django docs

GENRES = ('general', 'pop', 'dance', 'traditional', 'rock', 'alternative', 'rap', 'country',
          'jazz', 'gospel', 'latin', 'reggae', 'comedy', 'historical', 'action', 'animation',
          'documentary', 'family', 'adventure', 'fantasy', 'drama', 'crime', 'horror', 'music',
          'mystery', 'romance', 'sport', 'thriller', 'war', 'western', 'fiction', 'epic',
          'tragedy', 'parody', 'pastoral', 'culture', 'art', 'dance', 'drugs', 'social')


class MixerProvider(BaseProvider):

    """ Implement some mixer methods. """

    def __init__(self, generator):
        self.providers = []
        self.generator = generator

    def load(self, providers=PROVIDERS, locale=None):
        if locale is None:
            locale = self.generator.locale

        for pname in providers:
            pcls, lang_found = Factory._get_provider_class(pname, locale)
            provider = pcls(self.generator)
            provider.__provider__ = pname
            provider.__lang__ = lang_found
            self.generator.add_provider(provider)

    def big_integer(self):
        """ Get a big integer.

        Get integer from -9223372036854775808 to 9223372036854775807.

        """
        return self.generator.random_int(-9223372036854775808, 9223372036854775807)

    def ip_generic(self, protocol=None):
        """ Get IP (v4 or v6) address.

        :param protocol:
            Set protocol to 'ipv4' or 'ipv6'. Generate either IPv4 or
            IPv6 address if none.

        """
        if protocol == 'ipv4':
            return self.generator.ipv4()

        if protocol == 'ipv6':
            return self.generator.ipv6()

        return self.generator.ipv4() if self.generator.boolean() else self.generator.ipv6()

    def positive_decimal(self, **kwargs):
        """ Get a positive decimal. """
        return self.generator.pydecimal(positive=True, **kwargs)

    def positive_integer(self, max=2147483647):  # noqa
        """ Get a positive integer. """
        return self.random_int(0, max=max)  # noqa

    def small_integer(self, min=-SMALLINT, max=SMALLINT):  # noqa
        """ Get a positive integer. """
        return self.random_int(min=min, max=max)  # noqa

    def small_positive_integer(self, max=SMALLINT):  # noqa
        """ Get a positive integer. """
        return self.random_int(0, max=max)  # noqa

    @staticmethod
    def uuid():
        import uuid
        return str(uuid.uuid1())

    def genre(self):
        return self.random_element(GENRES)

    def percent(self):
        return self.random_int(0, 100)

    def percent_decimal(self):
        return dc.Decimal("0.%d" % self.random_int(0, 99)) + dc.Decimal('0.01')

    def title(self):
        words = self.generator.words(6)
        return " ".join(words).title()

    def coordinates(self):
        return (self.generator.latitude(), self.generator.longitude())

    def pybytes(self, size=20):
        return self.pystr(size).encode('utf-8')


class MixerGenerator(Generator):

    """ Support dynamic locales switch. """

    def __init__(self, locale=DEFAULT_LOCALE, providers=PROVIDERS, **config):
        self._locale = None
        self._envs = defaultdict(self.__create_env)
        self.locale = locale
        super(MixerGenerator, self).__init__(**config)
        self.env.load(providers)

    def __create_env(self):
        return MixerProvider(self)

    def __getattr__(self, name):
        return getattr(self.env, name)

    @property
    def providers(self):
        return self.env.providers

    @providers.setter
    def providers(self, value):
        self.env.providers = value

    @property
    def locale(self):
        return self._locale

    @locale.setter
    def locale(self, value):
        value = pylocale.normalize(value.replace('-', '_')).split('.')[0]
        if value not in AVAILABLE_LOCALES:
            value = DEFAULT_LOCALE

        if value == self._locale:
            return None

        nenv = self._envs[value]
        senv = self.env
        self._locale = value

        if senv.providers and not nenv.providers:
            nenv.load([p.__provider__ for p in senv.providers], value)

    @property
    def env(self):
        return self._envs[self._locale]

    def set_formatter(self, name, method):
        if not hasattr(self.env, name):
            setattr(self.env, name, method)


faker = MixerGenerator()
