import os

# Set Django settings before any other imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skyview.settings')
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["PYTHONPATH"] = os.getcwd()

from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

app = Celery('skyview')

# Get settings from Django
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure beat schedule
app.conf.beat_schedule = {
    'start-firehose-ingestion': {
        'task': 'ingestion.tasks.start_firehose_ingestion',
        'schedule': crontab(minute='*/1'),
    },
    'cleanup-old-events': {
        'task': 'ingestion.tasks.cleanup_old_events',
        'schedule': crontab(hour='*/1'),
    },
}

@app.task(bind=True)
def debug_task(self):
    logger.info(f'Request: {self.request!r}')

logger.info("Celery configuration complete")