import os
from django.conf import settings
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.local')

app = Celery('teams')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.timezone = 'UTC'

app.conf.beat_schedule = {
    'send-weekly-summary-every-monday-morning': {
        'task': 'apps.teams.tasks.send_weekly_summary',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Every Monday at 9:00 AM
    },
    'send-team-invitation': {
        'task': 'apps.teams.tasks.send_team_invitation',
        'schedule': crontab(hour=3, minute=0),  # Every day at 9:00 AM
    }
}