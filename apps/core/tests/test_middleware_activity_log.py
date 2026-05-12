import pytest
from django.test import Client

from apps.core.models import ActivityLog


@pytest.mark.django_db
def test_activity_log_written_on_request(client: Client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    log = ActivityLog.objects.latest("created_at")
    assert log.path == "/"
    assert log.method == "GET"
    assert log.status_code == 200
    assert log.request_id  # populated from RequestIDMiddleware


@pytest.mark.django_db
def test_activity_log_skips_static_and_healthz(client: Client) -> None:
    client.get("/healthz")
    assert not ActivityLog.objects.filter(path="/healthz").exists()
