import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import OwnerAllowlist

User = get_user_model()


@pytest.mark.django_db
def test_userprofile_auto_created_on_user_create() -> None:
    user = User.objects.create_user(
        username="a@example.com", email="a@example.com", password="x" * 14
    )
    assert hasattr(user, "profile")
    assert user.profile.is_approved is False
    assert user.profile.timezone == "Asia/Kolkata"


@pytest.mark.django_db
def test_user_with_owner_email_is_auto_approved() -> None:
    al = OwnerAllowlist.get_solo()
    al.emails = ["boss@example.com"]
    al.auto_approve = True
    al.save()
    user = User.objects.create_user(
        username="boss@example.com", email="boss@example.com", password="x" * 14
    )
    assert user.profile.is_approved is True


@pytest.mark.django_db
def test_non_owner_email_not_approved() -> None:
    user = User.objects.create_user(
        username="other@example.com", email="other@example.com", password="x" * 14
    )
    assert user.profile.is_approved is False
