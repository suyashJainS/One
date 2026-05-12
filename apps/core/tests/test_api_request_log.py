# apps/core/tests/test_api_request_log.py
import pytest

from apps.core.models import APIRequestLog


@pytest.mark.django_db
def test_access_token_redacted_on_save() -> None:
    log = APIRequestLog.objects.create(
        service="meta_api",
        method="GET",
        url="https://graph.facebook.com/v22.0/act_123/insights",
        query_params={"access_token": "EAAB123secret", "fields": "spend"},
        status_code=200,
        request_id="abc",
    )
    log.refresh_from_db()
    assert log.query_params["access_token"] == "[REDACTED]"
    assert log.query_params["fields"] == "spend"


@pytest.mark.django_db
def test_request_body_redaction() -> None:
    log = APIRequestLog.objects.create(
        service="meta_api",
        method="POST",
        url="https://graph.facebook.com/v22.0/act_123/campaigns",
        request_body={"access_token": "EAAB123", "name": "Test"},
        status_code=200,
    )
    log.refresh_from_db()
    assert log.request_body is not None
    assert log.request_body["access_token"] == "[REDACTED]"
