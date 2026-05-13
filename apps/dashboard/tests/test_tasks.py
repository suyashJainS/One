"""Tests for Celery tasks in the dashboard app (Phase J2)."""

from __future__ import annotations

import pytest
import respx
from django.core.cache import cache
from httpx import Response

from apps.clients.models import Client, ClientMetaCredentials, MetaAdAccount
from apps.dashboard.models import DailyMetricsCache


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def active_account(db):
    c = Client.objects.create(name="Acme", slug="acme", is_active=True)
    ClientMetaCredentials.objects.create(client=c, access_token="test-token")
    return MetaAdAccount.objects.create(
        client=c, account_id="act_42", currency="USD", is_active=True
    )


@pytest.mark.django_db
@respx.mock
def test_pull_writes_cache_row(active_account: MetaAdAccount) -> None:
    """pull_account_metrics (eager) fetches Meta insights and writes a SOURCE_BEAT row."""
    respx.get("https://graph.facebook.com/v22.0/act_42/insights").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {
                        "spend": "500.00",
                        "impressions": "5000",
                        "clicks": "100",
                        "cpm": "10.00",
                        "ctr": "2.0",
                        "frequency": "1.2",
                        "reach": "4000",
                        "outbound_clicks": [{"action_type": "outbound_click", "value": "80"}],
                        "outbound_clicks_ctr": [{"action_type": "outbound_click", "value": "1.6"}],
                        "actions": [
                            {"action_type": "landing_page_view", "value": "70"},
                            {"action_type": "add_to_cart", "value": "15"},
                            {"action_type": "purchase", "value": "5"},
                            {"action_type": "lead", "value": "12"},
                        ],
                        "action_values": [
                            {"action_type": "purchase", "value": "2500.00"},
                        ],
                        "date_start": "2026-05-12",
                        "date_stop": "2026-05-12",
                    }
                ]
            },
        )
    )

    from apps.dashboard.tasks import pull_account_metrics

    result = pull_account_metrics(account_id=active_account.account_id, date="2026-05-12")
    assert result == "act_42 2026-05-12 ok"

    row = DailyMetricsCache.objects.get(account=active_account, date="2026-05-12")
    assert row.source == DailyMetricsCache.SOURCE_BEAT
    assert row.spend == 500


@pytest.mark.django_db
def test_schedule_fans_out_to_active_accounts(monkeypatch) -> None:
    """schedule_daily_pulls dispatches exactly one task per active account."""
    # Active client + account
    active_client = Client.objects.create(name="Active Co", slug="active-co", is_active=True)
    active_account = MetaAdAccount.objects.create(
        client=active_client, account_id="act_active", currency="USD", is_active=True
    )

    # Inactive account (same active client)
    MetaAdAccount.objects.create(
        client=active_client, account_id="act_inactive_acct", currency="USD", is_active=False
    )

    # Active account but inactive client
    inactive_client = Client.objects.create(name="Inactive Co", slug="inactive-co", is_active=False)
    MetaAdAccount.objects.create(
        client=inactive_client, account_id="act_inactive_client", currency="USD", is_active=True
    )

    calls = []

    def fake_delay(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr("apps.dashboard.tasks.pull_account_metrics.delay", fake_delay)

    from apps.dashboard.tasks import schedule_daily_pulls

    count = schedule_daily_pulls()

    assert count == 1
    assert len(calls) == 1
    _, kwargs = calls[0]
    assert kwargs["account_id"] == active_account.account_id
