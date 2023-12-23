# File created to create a celery instance for all apps (like AlchemyApp) within the AlchemyProject Django project.
# Celery is a task queue with real-time processing - we use it today for updating progress bars on front end as the program runs on backend.
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AlchemyProject.settings')

app = Celery('AlchemyProject')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)