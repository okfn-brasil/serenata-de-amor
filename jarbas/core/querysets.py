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

    def list_distinct(self, field, order_by_field, query=None):
        if query:
            filter = {order_by_field + '__icontains': query}
            self = self.filter(**filter)

        self = self.values(field, order_by_field).order_by(order_by_field)
        return self.distinct()

    def tuple_filter(self, **kwargs):
        filters = self._to_tuple_filter(kwargs)
        for key, values in filters.items():
            filter_ = reduce(lambda q, val: q | Q(**{key: val}), values, Q())
            self = self.filter(filter_)
        return self

    @staticmethod
    def _to_tuple_filter(filters):
        rx = re.compile('[ ,]+')
        return {k: tuple(rx.split(v)) for k, v in filters.items()}
