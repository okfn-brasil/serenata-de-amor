from django.db import models


class SameDayQuerySet(models.QuerySet):

    def same_day(self, **kwargs):
        keys = ('year', 'applicant_id', 'document_id')
        unique_id = {k: v for k, v in kwargs.items()}
        if not all(map(unique_id.get, keys)):
            msg = 'A same_day queryset requires the kwargs: ' + ', '.join(keys)
            raise TypeError(msg)

        reference = self.get(**unique_id)
        return self.exclude(**unique_id).filter(
            issue_date=reference.issue_date,
            applicant_id=reference.applicant_id
        )
