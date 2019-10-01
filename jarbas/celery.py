import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jarbas.settings')

app = Celery('jarbas')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from django.core import management

    @app.task(ignore_result=True)
    def searchvector():
        print('Running searchvector...')
        management.call_command('searchvector')
        print('Searchvector is done')

    sender.add_periodic_task(
        crontab(minute='0', hour='2', day_of_month='*/2'),
        searchvector.s(),
    )
