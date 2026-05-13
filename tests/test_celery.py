"""Tests for the Celery application instance (Phase J1)."""

from __future__ import annotations


def test_celery_app_imports() -> None:
    from one import celery_app

    assert celery_app.main == "one"


def test_beat_schedule_contains_daily_pulls() -> None:
    from one import celery_app

    assert "schedule_daily_pulls" in celery_app.conf.beat_schedule
