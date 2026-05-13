from decimal import Decimal

import pytest

from apps.clients.models import Client, ClientMetaCredentials, MetaAdAccount


@pytest.mark.django_db
def test_create_client_with_credentials_and_account() -> None:
    client = Client.objects.create(name="Acme", slug="acme", target_roas=Decimal("3.0"))
    creds = ClientMetaCredentials.objects.create(client=client, access_token="EAAB123")
    account = MetaAdAccount.objects.create(
        client=client, account_id="act_999", account_name="Acme Main", currency="USD"
    )
    assert client.credentials == creds
    assert account.client == client


@pytest.mark.django_db
def test_access_token_encrypted_in_db() -> None:
    from django.db import connection

    client = Client.objects.create(name="Beam", slug="beam")
    ClientMetaCredentials.objects.create(client=client, access_token="EAAB-supersecret-XYZ")
    with connection.cursor() as cur:
        cur.execute(
            "SELECT access_token FROM clients_clientmetacredentials WHERE client_id = %s",
            [client.pk],
        )
        raw = cur.fetchone()[0]
    assert "EAAB-supersecret" not in str(raw)
    # Encrypted blobs are base64-y bytes; just confirm plaintext is not there.
    assert ClientMetaCredentials.objects.get(client=client).access_token == "EAAB-supersecret-XYZ"
