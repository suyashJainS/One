from __future__ import annotations

import pytest
from django.test import Client


@pytest.mark.django_db
def test_showroom_renders_in_dev(client: Client, settings: object) -> None:
    settings.DEBUG = True  # type: ignore[attr-defined]
    response = client.get("/design-system/")
    assert response.status_code == 200
    assert b"Buttons" in response.content
    assert b"Stat cards" in response.content


@pytest.mark.django_db
def test_showroom_hidden_in_prod(client: Client, settings: object) -> None:
    settings.DEBUG = False  # type: ignore[attr-defined]
    response = client.get("/design-system/")
    assert response.status_code == 404
