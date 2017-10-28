import re
from functools import reduce

from django.db import models
from django.db.models import Q


class ReimbursementQuerySet(models.QuerySet):

    def same_day_as(self, document_id):
        pk = dict(document_id=document_id)
        return self.exclude(**pk).filter(
            issue_date=self.filter(**pk).values('issue_date'),
            applicant_id=self.filter(**pk).values('applicant_id')
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

    def suspicions(self, boolean):
        if not boolean:
            return self.filter(suspicions=None)
        return self.exclude(suspicions=None)

    def has_receipt_url(self, boolean):
        if not boolean:
            return self.filter(receipt_url=None)
        return self.exclude(receipt_url=None)

    def in_latest_dataset(self, boolean):
        return self.filter(available_in_latest_dataset=boolean)

    def tuple_filter(self, **kwargs):
        filters = {_rename_key(k): v for k, v in _str_to_tuple(kwargs).items()}
        for key, values in filters.items():
            filter_ = reduce(lambda q, val: q | Q(**{key: val}), values, Q())
            self = self.filter(filter_)
        return self

    def was_ordered(self):
        return bool(self.query.order_by)


def _str_to_tuple(filters):
    """
    Transform string values from a dictionary into tuples. For example:
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
