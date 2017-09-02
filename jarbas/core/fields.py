from datetime import datetime

from rows.fields import DateField
from rows.fields import IntegerField as RowsIntegerField


class IntegerField(RowsIntegerField):

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        try:
            # Rows cannot convert values such as '2011.0' to integer
            value = float(value)
        except:
            pass
        return super(IntegerField, cls).deserialize(value)


class DateField(DateField):
    """
    Convert YYYY-MM-DDTHH:MM:SS to date object.
    """

    @classmethod
    def deserialize(cls, value, *args, **kwargs):
        try:
            return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S').date()
        except:
            return None
