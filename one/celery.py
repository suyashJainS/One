"""Celery application instance for the One project."""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "one.settings.dev")

app = Celery("one")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "schedule_daily_pulls": {
        "task": "apps.dashboard.tasks.schedule_daily_pulls",
        # 00:30 IST = 19:00 UTC previous day
        "schedule": crontab(hour=19, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):  # type: ignore[no-untyped-def]
    print(f"Request: {self.request!r}")
