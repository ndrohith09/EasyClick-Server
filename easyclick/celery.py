from __future__ import absolute_import,unicode_literals
import os
from celery.schedules import crontab
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE","easyclick.settings")


app=Celery("easyclick")
app.conf.enable_utc=False

app.conf.update(timezone="Asia/Kolkata")

app.config_from_object(settings,namespace="CELERY")


app.conf.beat_schedule = {
    'update-database': {
        'task': 'myapp.tasks.update_db',
        'schedule': crontab(minute="*/1"),
    
    }
    
}
app.autodiscover_tasks()
@app.task(bind=True)
def debug_task(self):
    print(f"Request:{self.request!r}")