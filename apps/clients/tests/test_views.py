import pytest
from django.contrib.auth import get_user_model
from django.test import Client as DjangoClient

from apps.clients.models import Client

User = get_user_model()


@pytest.fixture
def approved_user(db):
    user = User.objects.create_user(
        username="u@example.com", email="u@example.com", password="x" * 14
    )
    user.profile.is_approved = True
    user.profile.save()
    return user


@pytest.mark.django_db
def test_clients_list_requires_login(client: DjangoClient) -> None:
    response = client.get("/clients/")
    assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_clients_list_shows_clients(client: DjangoClient, approved_user) -> None:
    Client.objects.create(name="Acme", slug="acme")
    Client.objects.create(name="Beam", slug="beam", is_active=False)
    client.force_login(approved_user)
    response = client.get("/clients/")
    assert response.status_code == 200
    assert b"Acme" in response.content
    assert b"Beam" in response.content


@pytest.mark.django_db
def test_new_client_creates_record(client: DjangoClient, approved_user) -> None:
    client.force_login(approved_user)
    response = client.post(
        "/clients/new/",
        data={"name": "TestCo", "slug": "testco", "is_active": "on"},
        follow=True,
    )
    assert response.status_code == 200
    assert Client.objects.filter(slug="testco").exists()
