import logging
import os
from celery import Celery
from celery.schedules import crontab

from django.conf import settings

logger = logging.getLogger('celery')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarbas.settings')

app = Celery('jarbas')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from django.core import management

    @app.task(ignore_result=True)
    def searchvector():
        logger.info('Running searchvector...')
        management.call_command('searchvector')
        logger.info('Searchvector is done')

    if not settings.SCHEDULE_SEARCHVECTOR:
        return

    sender.add_periodic_task(
        crontab(
            minute=settings.SCHEDULE_SEARCHVECTOR_CRON_MINUTE,
            hour=settings.SCHEDULE_SEARCHVECTOR_CRON_HOUR,
            day_of_week=settings.SCHEDULE_SEARCHVECTOR_CRON_DAY_OF_WEEK,
            day_of_month=settings.SCHEDULE_SEARCHVECTOR_CRON_DAY_OF_MONTH,
            month_of_year=settings.SCHEDULE_SEARCHVECTOR_CRON_MONTH_OF_YEAR,
        ),
        searchvector.s(),
    )
