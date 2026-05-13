from collections.abc import Generator

import pytest
import respx
from django.core.cache import cache
from httpx import Response

from apps.clients.models import Client, ClientMetaCredentials, MetaAdAccount
from apps.core.models import APIRequestLog
from services.meta_api.client import MetaAPIClient
from services.meta_api.errors import AuthError, InvalidParamError, RateLimitError


@pytest.fixture(autouse=True)
def _clear_cache() -> Generator[None, None, None]:
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def account(db: None) -> MetaAdAccount:
    c = Client.objects.create(name="Acme", slug="acme")
    ClientMetaCredentials.objects.create(client=c, access_token="EAAB-secret")
    return MetaAdAccount.objects.create(client=c, account_id="act_1", currency="USD")


@pytest.mark.django_db
@respx.mock
def test_get_success_logs_request_with_token_redacted(account: MetaAdAccount) -> None:
    respx.get("https://graph.facebook.com/v22.0/act_1").mock(
        return_value=Response(200, json={"id": "act_1", "name": "Acme"})
    )
    client = MetaAPIClient()
    result = client.get(account, "/")
    assert result["name"] == "Acme"
    log = APIRequestLog.objects.latest("created_at")
    assert log.status_code == 200
    assert log.query_params["access_token"] == "[REDACTED]"


@pytest.mark.django_db
@respx.mock
def test_401_raises_auth_error(account: MetaAdAccount) -> None:
    respx.get("https://graph.facebook.com/v22.0/act_1").mock(
        return_value=Response(401, json={"error": {"code": 190, "message": "Invalid OAuth token"}})
    )
    client = MetaAPIClient()
    with pytest.raises(AuthError):
        client.get(account, "/")


@pytest.mark.django_db
@respx.mock
def test_400_code_4_raises_rate_limit(account: MetaAdAccount) -> None:
    respx.get("https://graph.facebook.com/v22.0/act_1").mock(
        return_value=Response(400, json={"error": {"code": 4, "message": "Rate limited"}})
    )
    client = MetaAPIClient()
    with pytest.raises(RateLimitError):
        client.get(account, "/")


@pytest.mark.django_db
@respx.mock
def test_transient_5xx_retries_then_succeeds(account: MetaAdAccount) -> None:
    route = respx.get("https://graph.facebook.com/v22.0/act_1")
    route.side_effect = [
        Response(503, json={"error": "server"}),
        Response(200, json={"name": "Acme"}),
    ]
    client = MetaAPIClient(max_retries=2, retry_backoff_seconds=0)
    result = client.get(account, "/")
    assert result["name"] == "Acme"


@pytest.mark.django_db
@respx.mock
def test_400_code_100_raises_invalid_param(account: MetaAdAccount) -> None:
    respx.get("https://graph.facebook.com/v22.0/act_1").mock(
        return_value=Response(400, json={"error": {"code": 100, "message": "Bad field"}})
    )
    client = MetaAPIClient()
    with pytest.raises(InvalidParamError):
        client.get(account, "/")


@pytest.mark.django_db
@respx.mock
def test_api_result_returned_even_if_log_write_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    c = Client.objects.create(name="Acme", slug="acme")
    ClientMetaCredentials.objects.create(client=c, access_token="T")
    account = MetaAdAccount.objects.create(client=c, account_id="act_1", currency="USD")
    respx.get("https://graph.facebook.com/v22.0/act_1").mock(
        return_value=Response(200, json={"name": "Acme"})
    )

    def _raise(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated log failure")

    from apps.core.models import APIRequestLog

    monkeypatch.setattr(APIRequestLog.objects, "create", _raise)
    result = MetaAPIClient().get(account, "/")
    assert result["name"] == "Acme"  # API result still returned despite logging failure
