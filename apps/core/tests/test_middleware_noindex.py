import pytest
from django.test import Client


@pytest.mark.django_db
def test_noindex_header_present(client: Client) -> None:
    response = client.get("/")
    assert response.headers.get("X-Robots-Tag") == "noindex, nofollow"
