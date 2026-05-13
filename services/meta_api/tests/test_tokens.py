import pytest
from django.test import override_settings

from apps.clients.models import Client, ClientMetaCredentials, MetaAdAccount
from services.meta_api.tokens import TokenNotFound, resolve_token


@pytest.fixture
def account(db: None) -> MetaAdAccount:
    client = Client.objects.create(name="Acme", slug="acme")
    return MetaAdAccount.objects.create(client=client, account_id="act_1", currency="USD")


@pytest.mark.django_db
def test_token_from_client_credentials(account: MetaAdAccount) -> None:
    ClientMetaCredentials.objects.create(client=account.client, access_token="CLIENT_TOK")
    assert resolve_token(account) == "CLIENT_TOK"


@pytest.mark.django_db
@override_settings(META_FALLBACK_TOKEN="ENV_TOK")
def test_token_from_env_when_no_client_creds(account: MetaAdAccount) -> None:
    assert resolve_token(account) == "ENV_TOK"


@pytest.mark.django_db
def test_token_missing_raises(account: MetaAdAccount) -> None:
    with pytest.raises(TokenNotFound):
        resolve_token(account)


@pytest.mark.django_db
def test_client_credentials_beat_env(account: MetaAdAccount) -> None:
    ClientMetaCredentials.objects.create(client=account.client, access_token="CLIENT_TOK")
    with override_settings(META_FALLBACK_TOKEN="ENV_TOK"):
        assert resolve_token(account) == "CLIENT_TOK"
