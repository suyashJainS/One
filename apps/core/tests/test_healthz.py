# apps/core/tests/test_healthz.py
import json

import pytest
from django.test import Client


@pytest.mark.django_db
def test_healthz_returns_200(client: Client) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload["status"] == "ok"
    assert payload["db"] == "ok"
    assert payload["cache"] == "ok"
