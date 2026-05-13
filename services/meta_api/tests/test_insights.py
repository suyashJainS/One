from collections.abc import Generator
from decimal import Decimal

import pytest
import respx
from django.core.cache import cache
from httpx import Response

from apps.clients.models import Client, ClientMetaCredentials, MetaAdAccount
from services.meta_api.insights import DailyInsights, fetch_daily_insights


@pytest.fixture(autouse=True)
def _clear_cache() -> Generator[None, None, None]:
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def account(db: None) -> MetaAdAccount:
    c = Client.objects.create(name="Acme", slug="acme")
    ClientMetaCredentials.objects.create(client=c, access_token="T")
    return MetaAdAccount.objects.create(client=c, account_id="act_42", currency="USD")


@pytest.mark.django_db
@respx.mock
def test_fetch_daily_insights_parses_response(account: MetaAdAccount) -> None:
    respx.get("https://graph.facebook.com/v22.0/act_42/insights").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {
                        "spend": "1234.56",
                        "impressions": "10000",
                        "clicks": "200",
                        "cpm": "12.34",
                        "ctr": "2.0",
                        "frequency": "1.5",
                        "reach": "8000",
                        "outbound_clicks": [{"action_type": "outbound_click", "value": "150"}],
                        "outbound_clicks_ctr": [{"action_type": "outbound_click", "value": "1.5"}],
                        "actions": [
                            {"action_type": "landing_page_view", "value": "120"},
                            {"action_type": "add_to_cart", "value": "30"},
                            {"action_type": "purchase", "value": "10"},
                            {"action_type": "lead", "value": "25"},
                        ],
                        "action_values": [
                            {"action_type": "purchase", "value": "4321.00"},
                        ],
                        "date_start": "2026-05-12",
                        "date_stop": "2026-05-12",
                    }
                ]
            },
        )
    )
    result = fetch_daily_insights(account, since="2026-05-12", until="2026-05-12")
    assert isinstance(result, DailyInsights)
    assert result.spend == Decimal("1234.56")
    assert result.impressions == 10000
    assert result.clicks == 200
    assert result.outbound_clicks == 150
    assert result.landing_page_views == 120
    assert result.add_to_cart == 30
    assert result.purchases == 10
    assert result.purchase_value == Decimal("4321.00")
    assert result.leads == 25


@pytest.mark.django_db
@respx.mock
def test_empty_data_returns_zeroed_insights(account: MetaAdAccount) -> None:
    respx.get("https://graph.facebook.com/v22.0/act_42/insights").mock(
        return_value=Response(200, json={"data": []})
    )
    result = fetch_daily_insights(account, since="2026-05-12", until="2026-05-12")
    assert result.spend == Decimal("0")
    assert result.impressions == 0
