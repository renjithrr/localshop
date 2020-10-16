from __future__ import absolute_import, unicode_literals
import os
from sys import stdout

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'localshop.settings.default')

app = Celery('localshop')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
stdout.write("Celery Up and running.\n")
# celery -A clal.settings worker -l info  has to run priorly in server
