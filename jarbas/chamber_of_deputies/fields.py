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
    INPUT_FORMAT = '%Y-%m-%d %H:%M:%S'
    OUTPUT_FORMAT = '%Y-%m-%d'

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        value = value.replace('T', ' ')  # normalize date/time separator
        return super(DateAsStringField, cls).deserialize(value)
