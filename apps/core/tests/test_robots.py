import pytest
from django.test import Client


@pytest.mark.django_db
def test_robots_txt_denies_all(client: Client) -> None:
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert b"User-agent: *" in response.content
    assert b"Disallow: /" in response.content
