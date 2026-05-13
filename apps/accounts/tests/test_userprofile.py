import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_userprofile_auto_created_on_user_create() -> None:
    user = User.objects.create_user(
        username="a@example.com", email="a@example.com", password="x" * 14
    )
    assert hasattr(user, "profile")
    assert user.profile.is_approved is False
    assert user.profile.timezone == "Asia/Kolkata"
