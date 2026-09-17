import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'securedocs.settings')

app = Celery('securedocs')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
