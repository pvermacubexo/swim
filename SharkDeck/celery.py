from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SharkDeck.settings')

app = Celery('SharkDeck', include=["SharkDeck.tasks"], broker='redis://localhost:6379/0')
# app = Celery('SharkDeck')

app.conf.beat_schedule = {
    'appointment_mail_send': {
        'task': 'SharkDeck.tasks.appointment_mail',
        'schedule': crontab(minute=0, hour=0)  # every day at midnight
    }
}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
