import json

from rows import fields


class FloatField(fields.FloatField):

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        try:  # Rows cannot convert values such as '14,96' to float
            value = float(value.replace(',', '.'))
        except:
            pass
        return super(FloatField, cls).deserialize(value)


class IntegerField(fields.IntegerField):

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        try:  # Rows cannot convert values such as '2011.0' to integer
            value = int(float(value))
        except:
            pass
        return super(IntegerField, cls).deserialize(value)


class DateAsStringField(fields.DateField):
    INPUT_FORMAT = '%Y-%m-%d %H:%M:%S'
    OUTPUT_FORMAT = '%Y-%m-%d'

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = value.replace('T', ' ')  # normalize date/time separator
        return super(DateAsStringField, cls).deserialize(value)


class ArrayField(fields.JSONField):
    TYPE = (list,)

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = value.replace('\'', '"').replace('nan', 'null')
        if value is None or isinstance(value, cls.TYPE):
            return value
        else:
            return json.loads(value)
