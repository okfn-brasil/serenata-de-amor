""" Mixer types. """

from copy import deepcopy


class BigInteger:

    """ Type for big integers. """

    pass


class EmailString:

    """ Type for emails. """

    pass


class HostnameString:

    """ Type for hostnames. """

    pass


class IP4String:

    """ Type for IPv4 addresses. """

    pass


class IP6String:

    """ Type for IPv6 addresses. """

    pass


class IPString:

    """ Type for IPv4 and IPv6 addresses. """

    pass


class NullOrBoolean:

    """ Type for None or boolean values. """

    pass


class PositiveDecimal:

    """ Type for positive decimals. """

    pass


class PositiveInteger:

    """ Type for positive integers. """

    pass


class PositiveSmallInteger:

    """ Type for positive small integers. """

    pass


class SmallInteger:

    """ Type for small integers. """

    pass


class Text:

    """ Type for texts. """

    pass


class URL:

    """ Type for URLs. """

    pass


class UUID:

    """ Type for UUIDs. """

    pass


class Mix(object):

    """ Virtual link on the mixed object.

    ::

        mixer = Mixer()

        # here `mixer.MIX` points on a generated `User` instance
        user = mixer.blend(User, username=mixer.MIX.first_name)

        # here `mixer.MIX` points on a generated `Message.author` instance
        message = mixer.blend(Message, author__name=mixer.MIX.login)

        # Mixer mix can get a function
        message = mixer.blend(Message, title=mixer.MIX.author(
            lambda author: 'Author: %s' % author.name
        ))

    """

    def __init__(self, value=None, parent=None):
        self.__value = value
        self.__parent = parent
        self.__func = None

    def __getattr__(self, value):
        return Mix(value, self if self.__value else None)

    def __call__(self, func):
        self.__func = func
        return self

    def __and__(self, values):
        if self.__parent:
            values = self.__parent & values
        if isinstance(values, dict):
            value = values[self.__value]
        elif isinstance(values, _Deffered):
            value = getattr(values.value, self.__value)
        else:
            value = getattr(values, self.__value)
        if self.__func:
            return self.__func(value)
        return value

    def __str__(self):
        return '%s/%s' % (self.__value, str(self.__parent or ''))

    def __repr__(self):
        return '<Mix %s>' % str(self)


class ServiceValue(object):

    """ Abstract class for mixer values. """

    def __init__(self, scheme=None, *choices, **params):
        self.scheme = scheme
        self.choices = choices
        self.params = params

    @classmethod
    def __call__(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def gen_value(self, type_mixer, name, field):
        """ Abstract method for value generation. """
        raise NotImplementedError


class Field(ServiceValue):

    """ Set field values.

    By default the mixer generates random or fake a field values by types
    of them. But you can set some values by manual.

    ::

        # Generate a User model
        mixer.blend(User)

        # Generate with some values
        mixer.blend(User, name='John Connor')

    .. note:: Value may be a callable or instance of generator.

    ::

        # Value may be callable
        client = mixer.blend(Client, username=lambda:'callable_value')
        assert client.username == 'callable_value'

        # Value may be a generator
        clients = mixer.cycle(4).blend(
            Client, username=(name for name in ('Piter', 'John')))


    .. seealso:: :class:`mixer.main.Fake`, :class:`mixer.main.Random`,
                 :class:`mixer.main.Select`,
                 :meth:`mixer.main.Mixer.sequence`

    """

    def __init__(self, scheme, name, **params):
        self.name = name
        super(Field, self).__init__(scheme, **params)

    def __deepcopy__(self, memo):
        return Field(self.scheme, self.name, **deepcopy(self.params))

    def gen_value(self, type_mixer, name, field):
        """ Call :meth:`TypeMixer.gen_field`.

        :return value: A generated value

        """
        return type_mixer.gen_field(field)


# Service classes
class Fake(ServiceValue):

    """ Force a `fake` value.

    If you initialized a :class:`~mixer.main.Mixer` with `fake=False` you can
    force a `fake` value for field with this attribute (mixer.FAKE).

    ::

         mixer = Mixer(fake=False)
         user = mixer.blend(User)
         print user.name  # Some like: Fdjw4das

         user = mixer.blend(User, name=mixer.FAKE)
         print user.name  # Some like: Bob Marley

    You can setup a field type for generation of fake value: ::

         user = mixer.blend(User, score=mixer.FAKE(str))
         print user.score  # Some like: Bob Marley

    .. note:: This is also usefull on ORM model generation for filling a fields
              with default values (or null).

    ::

        from mixer.backend.django import mixer

        user = mixer.blend('auth.User', first_name=mixer.FAKE)
        print user.first_name  # Some like: John

    """

    def gen_value(self, type_mixer, name, fake):
        """ Call :meth:`TypeMixer.gen_fake`.

        :return value: A generated value

        """
        return type_mixer.gen_fake(name, fake)


class Random(ServiceValue):

    """ Force a `random` value.

    If you initialized a :class:`~mixer.main.Mixer` by default mixer try to
    fill fields with `fake` data. You can user `mixer.RANDOM` for prevent this
    behaviour for a custom fields.

    ::

         mixer = Mixer()
         user = mixer.blend(User)
         print user.name  # Some like: Bob Marley

         user = mixer.blend(User, name=mixer.RANDOM)
         print user.name  # Some like: Fdjw4das

    You can setup a field type for generation of fake value: ::

         user = mixer.blend(User, score=mixer.RANDOM(str))
         print user.score  # Some like: Fdjw4das

    Or you can get random value from choices: ::

        user = mixer.blend(User, name=mixer.RANDOM('john', 'mike'))
         print user.name  # mike or john

    .. note:: This is also useful on ORM model generation for randomize fields
              with default values (or null).

    ::

        from mixer.backend.django import mixer

        mixer.blend('auth.User', first_name=mixer.RANDOM)
        print user.first_name  # Some like: Fdjw4das

    """

    def __init__(self, scheme=None, *choices, **params):
        super(Random, self).__init__(scheme, *choices, **params)
        if scheme is not None:
            self.choices += scheme,

    def gen_value(self, type_mixer, name, random):
        """ Call :meth:`TypeMixer.gen_random`.

        :return value: A generated value

        """
        return type_mixer.gen_random(name, random)


class Select(Random):

    """ Select values from database.

    When you generate some ORM models you can set value for related fields
    from database (select by random).

    Example for Django (select user from exists): ::

        from mixer.backend.django import mixer

        mixer.generate(Role, user=mixer.SELECT)


    You can setup a Django or SQLAlchemy filters with `mixer.SELECT`: ::

        from mixer.backend.django import mixer

        mixer.generate(Role, user=mixer.SELECT(
            username='test'
        ))

    """

    def gen_value(self, type_mixer, name, field):
        """ Call :meth:`TypeMixer.gen_random`.

        :return value: A generated value

        """
        return type_mixer.gen_select(name, field)


class _Deffered(object):

    """ A type which will be generated later. """

    def __init__(self, value, scheme=None):
        self.value = value
        self.scheme = scheme
