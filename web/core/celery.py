import os

from celery import Celery
from . import settings 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.core.settings')

app = Celery('app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.timezone = 'Europe/Moscow'

app.conf.beat_schedule = {
    'schedule-notifications': {
        'task': 'web.protocols.tasks.set_notifications',
        'schedule': settings.SET_NOTIFICATIONS_SCHEDULE, 
    },

}