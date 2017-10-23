from datetime import date

from rows import fields


class IntegerField(fields.IntegerField):

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        try:  # Rows cannot convert values such as '2011.0' to integer
            value = int(float(value))
        except:
            pass
        return super(IntegerField, cls).deserialize(value)


class DateAsStringField(fields.DateField):
    INPUT_FORMAT = '%Y-%m-%dT%H:%M:%S'
    OUTPUT_FORMAT = '%Y-%m-%d'

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = super(DateAsStringField, cls).deserialize(value)
        if value:  # useful when serializing it to Celery
            return value.strftime(cls.OUTPUT_FORMAT)
