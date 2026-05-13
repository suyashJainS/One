"""Phase I creates the synchronous helper. Phase J adds the Celery task wrapper."""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from celery import shared_task
from django.utils import timezone

from apps.clients.models import MetaAdAccount
from services.meta_api.client import MetaAPIClient
from services.meta_api.errors import AuthError
from services.meta_api.insights import fetch_daily_insights

from .models import DailyMetricsCache

logger = logging.getLogger(__name__)


def pull_account_metrics_sync(
    account_id: str,
    date: str,
    source: str = DailyMetricsCache.SOURCE_BEAT,
) -> str:
    """Fetch a single day's metrics from Meta and upsert the cache row.

    Synchronous helper used by the dashboard HTMX refresh button (source="manual")
    and by the Celery beat task (source="beat", the default).
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
        source=source,
    )
    account.last_sync_at = timezone.now()
    account.last_error = ""
    account.save(update_fields=["last_sync_at", "last_error"])
    return f"{account_id} {date} ok"


@shared_task(bind=True, max_retries=5, default_retry_delay=60)  # type: ignore[untyped-decorator]
def pull_account_metrics(self: Any, account_id: str, date: str) -> str:
    """Celery task wrapper around the synchronous helper.

    Retries on rate-limit (countdown from exception); auth errors mark
    the account and surface to Sentry.
    """
    from services.meta_api.errors import AuthError, RateLimitError

    try:
        return pull_account_metrics_sync(
            account_id=account_id, date=date, source=DailyMetricsCache.SOURCE_BEAT
        )
    except RateLimitError as exc:
        raise self.retry(exc=exc, countdown=getattr(exc, "retry_after_seconds", 60)) from exc
    except AuthError:
        raise  # last_error already set in the sync helper


@shared_task  # type: ignore[untyped-decorator]
def schedule_daily_pulls() -> int:
    """Fan out a pull_account_metrics.delay() per active account for yesterday's date."""
    yesterday = (timezone.localdate() - dt.timedelta(days=1)).isoformat()
    count = 0
    for account in MetaAdAccount.objects.filter(is_active=True, client__is_active=True):
        pull_account_metrics.delay(account_id=account.account_id, date=yesterday)
        count += 1
    return count
