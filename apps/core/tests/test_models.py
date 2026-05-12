# apps/core/tests/test_models.py
import pytest

from apps.core.models import ActivityLog


@pytest.mark.django_db
def test_activity_log_minimum_fields() -> None:
    log = ActivityLog.objects.create(
        level="info",
        action="page_view",
        path="/",
        method="GET",
        status_code=200,
        ip_address="127.0.0.1",
        duration_ms=12,
        request_id="abc",
    )
    assert log.pk
    assert log.created_at is not None
