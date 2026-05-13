import pytest
from django.contrib.auth import get_user_model
from django.test import Client as DjangoClient
from django.urls import reverse

from apps.clients.models import Client, MetaAdAccount

User = get_user_model()


@pytest.mark.django_db
def test_admin_can_add_account(client: DjangoClient) -> None:
    admin = User.objects.create_superuser(username="a@x", email="a@x", password="x" * 14)
    client.force_login(admin)
    c = Client.objects.create(name="Acme", slug="acme")
    response = client.post(
        reverse("admin:clients_metaadaccount_add"),
        data={
            "client": c.pk,
            "account_id": "act_42",
            "account_name": "Acme USD",
            "currency": "USD",
            "timezone_offset": 0,
            "is_active": "on",
        },
    )
    assert response.status_code in (200, 302)
    assert MetaAdAccount.objects.filter(account_id="act_42").exists()
