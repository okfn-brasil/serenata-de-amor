import os
from celery import Celery

#importing jarbas

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarbas.settings')

app = Celery('jarbas')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
