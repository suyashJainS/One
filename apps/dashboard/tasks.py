"""Phase I creates the synchronous helper. Phase J adds the Celery task wrapper."""

from __future__ import annotations

import datetime as dt
import logging

from django.utils import timezone

from apps.clients.models import MetaAdAccount
from services.meta_api.client import MetaAPIClient
from services.meta_api.errors import AuthError
from services.meta_api.insights import fetch_daily_insights

from .models import DailyMetricsCache

logger = logging.getLogger(__name__)


def pull_account_metrics_sync(account_id: str, date: str) -> str:
    """Fetch a single day's metrics from Meta and upsert the cache row.

    Synchronous helper used by the dashboard HTMX refresh button.
    Phase J wraps a Celery task around this for nightly fan-out.
    """
    account = MetaAdAccount.objects.select_related("client").get(account_id=account_id)
    try:
        insights = fetch_daily_insights(account, since=date, until=date, client=MetaAPIClient())
    except AuthError as exc:
        account.last_error = f"AuthError: {exc}"
        account.save(update_fields=["last_error"])
        raise
    DailyMetricsCache.upsert(
        account=account,
        date=dt.date.fromisoformat(date),
        spend=insights.spend,
        impressions=insights.impressions,
        clicks=insights.clicks,
        cpm=insights.cpm,
        ctr=insights.ctr,
        frequency=insights.frequency,
        reach=insights.reach,
        outbound_clicks=insights.outbound_clicks,
        outbound_clicks_ctr=insights.outbound_clicks_ctr,
        landing_page_views=insights.landing_page_views,
        add_to_cart=insights.add_to_cart,
        purchases=insights.purchases,
        purchase_value=insights.purchase_value,
        leads=insights.leads,
        source=DailyMetricsCache.SOURCE_BEAT,
    )
    account.last_sync_at = timezone.now()
    account.last_error = ""
    account.save(update_fields=["last_sync_at", "last_error"])
    return f"{account_id} {date} ok"
