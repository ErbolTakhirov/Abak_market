# ==============================================
# CELERY CONFIGURATION
# ==============================================
"""
Celery application configuration for async task processing.
Handles voice messages, PDF generation, notifications.
"""

import os
from celery import Celery
from celery.signals import task_failure, task_success, task_prerun
from django.conf import settings
import logging

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery application
app = Celery('grocery_store')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configure queues
app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'voice': {
        'exchange': 'voice',
        'routing_key': 'voice',
    },
    'pdf': {
        'exchange': 'pdf',
        'routing_key': 'pdf',
    },
    'notifications': {
        'exchange': 'notifications',
        'routing_key': 'notifications',
    },
}

app.conf.task_default_queue = 'default'

# Task configuration
app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Autodiscover tasks from all installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Logging
logger = logging.getLogger('celery')


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Log task start."""
    logger.info(f'Task {task.name}[{task_id}] starting with args={args}')


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Log successful task completion."""
    logger.info(f'Task {sender.name} completed successfully')


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """Log failed task with traceback."""
    logger.error(
        f'Task {sender.name}[{task_id}] failed: {exception}',
        exc_info=True
    )


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connection."""
    print(f'Request: {self.request!r}')
