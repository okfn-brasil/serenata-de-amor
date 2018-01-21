""" Support for Pony ODM.

::

    from mixer.backend.pony import mixer
"""
from __future__ import absolute_import

from pony.orm import commit

from .. import mix_types as t
from ..main import TypeMixer as BaseTypeMixer, Mixer as BaseMixer, SKIP_VALUE


class TypeMixer(BaseTypeMixer):

    """ TypeMixer for Pony ORM. """

    def __load_fields(self):
        for attr in self.__scheme._attrs_:
            yield attr.column, t.Field(attr, attr.column)

    def populate_target(self, values):
        """ Populate target. """
        return self.__scheme(**dict(values))

    def is_required(self, field):
        """ Return True is field's value should be defined.

        :return bool:

        """
        return field.scheme.is_required and not field.scheme.is_pk

    def is_unique(self, field):
        """ Return True is field's value should be a unique.

        :return bool:

        """
        return field.scheme.is_unique

    @staticmethod
    def get_default(field):
        """ Get default value from field.

        :return value:

        """
        return field.scheme.default is None and SKIP_VALUE or field.scheme.default # noqa

    def make_fabric(self, field, field_name=None, fake=False, kwargs=None): # noqa
        """ Make values fabric for column.

        :param column: SqlAlchemy column
        :param field_name: Field name
        :param fake: Force fake data

        :return function:

        """
        py_type = field.py_type
        return super(TypeMixer, self).make_fabric(
            py_type, field_name=field_name, fake=fake, kwargs=kwargs)


class Mixer(BaseMixer):

    """ Integration with Pony ORM. """

    type_mixer_cls = TypeMixer

    def postprocess(self, target):
        """ Save objects in db.

        :return value: A generated value

        """
        if self.params.get('commit'):
            commit()

        return target


# Default Pony mixer
mixer = Mixer()

# pylama:ignore=E1120
