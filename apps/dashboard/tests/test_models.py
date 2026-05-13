from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from apps.clients.models import Client, MetaAdAccount
from apps.dashboard.models import DailyMetricsCache


@pytest.fixture
def account(db: None) -> MetaAdAccount:
    c = Client.objects.create(name="Acme", slug="acme")
    return MetaAdAccount.objects.create(client=c, account_id="act_1", currency="USD")


@pytest.mark.django_db
def test_upsert_creates_then_updates(account: MetaAdAccount) -> None:
    today = dt.date(2026, 5, 12)
    DailyMetricsCache.upsert(
        account=account, date=today, spend=Decimal("100"), impressions=1000, source="manual"
    )
    DailyMetricsCache.upsert(
        account=account, date=today, spend=Decimal("150"), impressions=1500, source="beat"
    )
    row = DailyMetricsCache.objects.get(account=account, date=today)
    assert row.spend == Decimal("150")
    assert row.impressions == 1500
    assert row.source == "beat"


@pytest.mark.django_db
def test_computed_properties(account: MetaAdAccount) -> None:
    today = dt.date(2026, 5, 12)
    row = DailyMetricsCache.objects.create(
        account=account,
        date=today,
        spend=Decimal("200"),
        purchases=10,
        purchase_value=Decimal("600"),
        leads=20,
        source="manual",
    )
    assert row.cost_per_purchase == Decimal("20")
    assert row.cost_per_lead == Decimal("10")
    assert row.roas == Decimal("3")


@pytest.mark.django_db
def test_zero_spend_safe_props(account: MetaAdAccount) -> None:
    today = dt.date(2026, 5, 12)
    row = DailyMetricsCache.objects.create(account=account, date=today, source="manual")
    assert row.cost_per_purchase is None
    assert row.cost_per_lead is None
    assert row.roas is None


@pytest.mark.django_db
def test_upsert_no_duplicate(account: MetaAdAccount) -> None:
    today = dt.date(2026, 5, 12)
    DailyMetricsCache.upsert(account=account, date=today, spend=Decimal("100"))
    DailyMetricsCache.upsert(account=account, date=today, spend=Decimal("200"))
    assert DailyMetricsCache.objects.filter(account=account, date=today).count() == 1


@pytest.mark.django_db
def test_str_representation(account: MetaAdAccount) -> None:
    today = dt.date(2026, 5, 12)
    row = DailyMetricsCache.objects.create(account=account, date=today, source="manual")
    assert str(row) == "act_1 2026-05-12"
