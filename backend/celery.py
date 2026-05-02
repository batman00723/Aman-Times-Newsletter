import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

# The namespace='CELERY' tells it to look for CELERY_ in settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# This searches your apps for tasks.py files
app.autodiscover_tasks()