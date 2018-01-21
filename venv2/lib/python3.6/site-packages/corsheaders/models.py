from django.db import models

# For signal registration
from .signals import check_request_enabled  # noqa


class CorsModel(models.Model):
    cors = models.CharField(max_length=255)
