from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import QuerySet, Sum
from django.utils import timezone

from apps.clients.models import MetaAdAccount

from .models import DailyMetricsCache


@dataclass
class KPIs:
    spend: Decimal = Decimal("0")
    purchases: int = 0
    purchase_value: Decimal = Decimal("0")
    leads: int = 0
    clicks: int = 0
    impressions: int = 0

    @property
    def cpl(self) -> Decimal | None:
        return (self.spend / self.leads) if self.leads else None

    @property
    def cpp(self) -> Decimal | None:
        return (self.spend / self.purchases) if self.purchases else None

    @property
    def roas(self) -> Decimal | None:
        return (self.purchase_value / self.spend) if self.spend else None


@dataclass
class ClientSummary:
    client_id: int
    client_name: str
    client_slug: str
    accounts: list[MetaAdAccount] = field(default_factory=list)
    today: KPIs = field(default_factory=KPIs)
    yesterday: KPIs = field(default_factory=KPIs)
    has_data: bool = False


def _aggregate(qs: QuerySet[DailyMetricsCache]) -> KPIs:
    data = qs.aggregate(
        spend=Sum("spend"),
        purchases=Sum("purchases"),
        purchase_value=Sum("purchase_value"),
        leads=Sum("leads"),
        clicks=Sum("clicks"),
        impressions=Sum("impressions"),
    )
    return KPIs(
        spend=data["spend"] or Decimal("0"),
        purchases=data["purchases"] or 0,
        purchase_value=data["purchase_value"] or Decimal("0"),
        leads=data["leads"] or 0,
        clicks=data["clicks"] or 0,
        impressions=data["impressions"] or 0,
    )


def overview_data(today: dt.date | None = None) -> dict[str, object]:
    today = today or timezone.localdate()
    yesterday = today - dt.timedelta(days=1)

    accounts = MetaAdAccount.objects.filter(is_active=True, client__is_active=True).select_related(
        "client"
    )
    cache_today = DailyMetricsCache.objects.filter(account__in=accounts, date=today)
    cache_yest = DailyMetricsCache.objects.filter(account__in=accounts, date=yesterday)

    kpi_today = _aggregate(cache_today)
    kpi_yest = _aggregate(cache_yest)

    by_client: dict[int, ClientSummary] = {}
    for account in accounts:
        summary = by_client.setdefault(
            account.client_id,
            ClientSummary(
                client_id=account.client_id,
                client_name=account.client.name,
                client_slug=account.client.slug,
            ),
        )
        summary.accounts.append(account)
    for row in cache_today:
        s = by_client.get(row.account.client_id)
        if s:
            s.today.spend += row.spend
            s.today.purchases += row.purchases
            s.today.purchase_value += row.purchase_value
            s.today.leads += row.leads
            s.today.clicks += row.clicks
            s.today.impressions += row.impressions
            s.has_data = True
    for row in cache_yest:
        s = by_client.get(row.account.client_id)
        if s:
            s.yesterday.spend += row.spend
            s.yesterday.purchases += row.purchases
            s.yesterday.purchase_value += row.purchase_value
            s.yesterday.leads += row.leads
            s.has_data = True

    return {
        "today": today,
        "yesterday": yesterday,
        "kpi_today": kpi_today,
        "kpi_yesterday": kpi_yest,
        "clients": sorted(by_client.values(), key=lambda c: c.client_name.lower()),
    }
