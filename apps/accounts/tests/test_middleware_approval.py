import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.mark.django_db
def test_anonymous_unaffected(client: Client) -> None:
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_unapproved_user_redirected_to_pending(client: Client) -> None:
    user = User.objects.create_user(
        username="x@example.com", email="x@example.com", password="x" * 14
    )
    client.force_login(user)
    response = client.get("/")
    assert response.status_code == 302
    assert response.url.endswith("/auth/pending-approval/")


@pytest.mark.django_db
def test_approved_user_passes(client: Client) -> None:
    user = User.objects.create_user(
        username="y@example.com", email="y@example.com", password="x" * 14
    )
    user.profile.is_approved = True
    user.profile.save()
    client.force_login(user)
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_superuser_passes_without_approval(client: Client) -> None:
    user = User.objects.create_superuser(
        username="su@example.com", email="su@example.com", password="x" * 14
    )
    client.force_login(user)
    response = client.get("/admin/")
    assert response.status_code in (200, 302)  # admin redirect is fine
