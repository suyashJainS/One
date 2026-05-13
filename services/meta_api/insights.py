"""Daily insights fetch + parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from apps.clients.models import MetaAdAccount

from .client import MetaAPIClient

INSIGHTS_FIELDS = ",".join(
    [
        "spend",
        "impressions",
        "clicks",
        "cpm",
        "ctr",
        "frequency",
        "reach",
        "outbound_clicks",
        "outbound_clicks_ctr",
        "actions",
        "action_values",
        "date_start",
        "date_stop",
    ]
)

# Action-type names we sum into our flat fields
_ACTION_LP_VIEW = "landing_page_view"
_ACTION_ATC = "add_to_cart"
_ACTION_PURCHASE = "purchase"
_ACTION_LEAD = "lead"
_ACTION_OUTBOUND_CLICK = "outbound_click"


@dataclass
class DailyInsights:
    spend: Decimal = Decimal("0")
    impressions: int = 0
    clicks: int = 0
    cpm: Decimal = Decimal("0")
    ctr: Decimal = Decimal("0")
    frequency: Decimal = Decimal("0")
    reach: int = 0
    outbound_clicks: int = 0
    outbound_clicks_ctr: Decimal = Decimal("0")
    landing_page_views: int = 0
    add_to_cart: int = 0
    purchases: int = 0
    purchase_value: Decimal = Decimal("0")
    leads: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


def _d(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _i(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(Decimal(str(value)))
    except Exception:
        return 0


def _sum_action(actions: list[dict[str, Any]] | None, name: str) -> int:
    if not actions:
        return 0
    total = 0
    for a in actions:
        if a.get("action_type") == name:
            total += _i(a.get("value"))
    return total


def _sum_action_decimal(actions: list[dict[str, Any]] | None, name: str) -> Decimal:
    if not actions:
        return Decimal("0")
    total = Decimal("0")
    for a in actions:
        if a.get("action_type") == name:
            total += _d(a.get("value"))
    return total


def fetch_daily_insights(
    account: MetaAdAccount,
    since: str,
    until: str,
    client: MetaAPIClient | None = None,
) -> DailyInsights:
    api = client or MetaAPIClient()
    body = api.get(
        account,
        "insights",
        params={
            "fields": INSIGHTS_FIELDS,
            "time_range": f'{{"since":"{since}","until":"{until}"}}',
            "level": "account",
        },
    )
    rows = body.get("data") if isinstance(body, dict) else None
    if not rows:
        return DailyInsights()
    row = rows[0]
    return DailyInsights(
        spend=_d(row.get("spend")),
        impressions=_i(row.get("impressions")),
        clicks=_i(row.get("clicks")),
        cpm=_d(row.get("cpm")),
        ctr=_d(row.get("ctr")),
        frequency=_d(row.get("frequency")),
        reach=_i(row.get("reach")),
        outbound_clicks=_sum_action(row.get("outbound_clicks"), _ACTION_OUTBOUND_CLICK),
        outbound_clicks_ctr=_sum_action_decimal(
            row.get("outbound_clicks_ctr"), _ACTION_OUTBOUND_CLICK
        ),
        landing_page_views=_sum_action(row.get("actions"), _ACTION_LP_VIEW),
        add_to_cart=_sum_action(row.get("actions"), _ACTION_ATC),
        purchases=_sum_action(row.get("actions"), _ACTION_PURCHASE),
        purchase_value=_sum_action_decimal(row.get("action_values"), _ACTION_PURCHASE),
        leads=_sum_action(row.get("actions"), _ACTION_LEAD),
        raw=row,
    )
