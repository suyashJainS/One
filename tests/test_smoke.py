import pytest
from django.test import Client


@pytest.mark.django_db
def test_root_renders_base_template(client: Client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert b"One" in response.content
    assert b"csrf-token" in response.content
