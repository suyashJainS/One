# apps/core/tests/test_middleware_request_id.py
import pytest
from django.test import Client


@pytest.mark.django_db
def test_request_id_added_to_request(client: Client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 36  # UUID v4 length
