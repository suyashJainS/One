import pytest

from apps.accounts.models import OwnerAllowlist


@pytest.mark.django_db
def test_allowlist_is_singleton() -> None:
    a = OwnerAllowlist.get_solo()
    b = OwnerAllowlist.get_solo()
    assert a.pk == b.pk
    a.emails = ["owner@example.com"]
    a.save()
    assert OwnerAllowlist.get_solo().emails == ["owner@example.com"]


@pytest.mark.django_db
def test_email_is_owner_helper() -> None:
    al = OwnerAllowlist.get_solo()
    al.emails = ["Owner@Example.com"]
    al.auto_approve = True
    al.save()
    assert OwnerAllowlist.is_owner("owner@example.com")
    assert OwnerAllowlist.is_owner("OWNER@example.com")
    assert not OwnerAllowlist.is_owner("nobody@example.com")
