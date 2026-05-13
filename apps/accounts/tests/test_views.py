import pytest
from django.test import Client


@pytest.mark.django_db
def test_pending_approval_page_renders(client: Client) -> None:
    response = client.get("/auth/pending-approval/")
    assert response.status_code == 200
    assert b"pending" in response.content.lower()
