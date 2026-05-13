# apps/core/tests/test_middleware_request_id.py
import pytest
from django.test import Client


@pytest.mark.django_db
def test_request_id_added_to_request(client: Client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 36  # UUID v4 length


@pytest.mark.django_db
def test_incoming_request_id_is_honored(client: Client) -> None:
    response = client.get("/", HTTP_X_REQUEST_ID="my-trace-id")
    assert response.headers["X-Request-ID"] == "my-trace-id"


@pytest.mark.django_db
def test_incoming_request_id_is_truncated_at_64_chars(client: Client) -> None:
    long_id = "a" * 200
    response = client.get("/", HTTP_X_REQUEST_ID=long_id)
    returned = response.headers["X-Request-ID"]
    assert len(returned) == 64
    assert returned == long_id[:64]
