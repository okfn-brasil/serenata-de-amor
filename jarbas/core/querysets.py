import re
from functools import reduce

from django.db import models
from django.db.models import Q


class ReimbursementQuerySet(models.QuerySet):

    def same_day(self, **kwargs):
        keys = ('year', 'applicant_id', 'document_id')
        unique_id = {k: v for k, v in kwargs.items()}
        if not all(map(unique_id.get, keys)):
            msg = 'A same_day queryset requires the kwargs: ' + ', '.join(keys)
            raise TypeError(msg)

        return self.exclude(**unique_id).filter(
            issue_date=self.filter(**unique_id).values('issue_date'),
            applicant_id=unique_id['applicant_id']
        )

    def order_by_probability(self):
        kwargs = {
            'select': {'probability_is_null': 'probability IS NULL'},
            'order_by': ['probability_is_null', '-probability']
        }
        return self.extra(**kwargs)

    def list_distinct(self, field, order_by_field, query=None):
        if query:
            filter = {order_by_field + '__icontains': query}
            self = self.filter(**filter)

        self = self.values(field, order_by_field).order_by(order_by_field)
        return self.distinct()

    def tuple_filter(self, **kwargs):
        filters = {_rename_key(k): v for k, v in _str_to_tuple(kwargs).items()}
        for key, values in filters.items():
            filter_ = reduce(lambda q, val: q | Q(**{key: val}), values, Q())
            self = self.filter(filter_)
        return self


def _str_to_tuple(filters):
    """
    Transform string values form a dictionary in tuples. For example:
            {
            'document': '42,3',
            'year': '1994,1996',
            'applicant': '1'
        }

    Becomes:
            {
            'document': (42, 3),
            'year': (1994, 1996),
            'applicant': (1, ),
        }
    """
    rx = re.compile('[ ,]+')
    return {k: tuple(rx.split(v)) for k, v in filters.items()}


def _rename_key(key):
    mapping = dict(
        issue_date_start='issue_date__gte',
        issue_date_end='issue_date__lt'
    )
    return mapping.get(key, key)
