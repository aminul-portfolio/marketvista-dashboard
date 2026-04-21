from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module for 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketvista.settings')

app = Celery('marketvista')

# Load Celery config from Django settings with CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in installed apps
app.autodiscover_tasks()

# Schedule periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'fetch-snapshots-every-minute': {
        'task': 'monitoring.tasks.fetch_snapshot_prices',  # ✅ Correct function name
        'schedule': crontab(),  # every 1 minute
    },
    'fetch-ohlc-every-minute': {
        'task': 'monitoring.tasks.fetch_and_store_ohlc',
        'schedule': crontab(),  # every 1 minute
    },
}

