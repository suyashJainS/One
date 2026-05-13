"""End-to-end check: Meta access tokens must never appear in APIRequestLog."""

import json

import pytest
import respx
from django.core.cache import cache
from httpx import Response

from apps.clients.models import Client, ClientMetaCredentials, MetaAdAccount
from apps.core.models import APIRequestLog
from services.meta_api.client import MetaAPIClient


@pytest.mark.django_db
@respx.mock
def test_no_token_in_logs_after_call() -> None:
    cache.clear()
    c = Client.objects.create(name="Acme", slug="acme")
    ClientMetaCredentials.objects.create(client=c, access_token="EAAB-this-must-not-leak-XYZ")
    account = MetaAdAccount.objects.create(client=c, account_id="act_1", currency="USD")
    respx.get("https://graph.facebook.com/v22.0/act_1").mock(
        return_value=Response(200, json={"id": "act_1"})
    )
    MetaAPIClient().get(account, "/")
    for row in APIRequestLog.objects.all():
        serialized = json.dumps(
            {
                "url": row.url,
                "params": row.query_params,
                "body": row.request_body,
                "response": row.response_body,
                "error": row.error,
            }
        )
        assert "EAAB-this-must-not-leak-XYZ" not in serialized
