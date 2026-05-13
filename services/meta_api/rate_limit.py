"""Track Meta API rate-limit signals via Redis cache."""

from __future__ import annotations

import json
import time

from django.core.cache import cache

_KEY = "meta_api:cooldown:{account_id}"
_DEFAULT_RETRY_AFTER = 60


def _key(account_id: str) -> str:
    return _KEY.format(account_id=account_id)


def in_cooldown(account_id: str) -> bool:
    return cache.get(_key(account_id)) is not None


def cooldown_seconds(account_id: str) -> int:
    expiry = cache.get(_key(account_id))
    if not expiry:
        return 0
    return max(0, int(expiry - time.time()))


def record_throttle(account_id: str, retry_after: int = _DEFAULT_RETRY_AFTER) -> None:
    cache.set(_key(account_id), time.time() + retry_after, retry_after)


def record_usage(account_id: str, header_value: str | None) -> None:
    """Parse X-Business-Use-Case-Usage / X-Ad-Account-Usage header.

    If any usage metric crosses 90%, start a cooldown using the suggested
    ``estimated_time_to_regain_access`` (or 60 s if not provided).
    """
    if not header_value:
        return
    try:
        data = json.loads(header_value)
    except json.JSONDecodeError:
        return
    items = data.items() if isinstance(data, dict) else []
    for _, entry in items:
        entries = entry if isinstance(entry, list) else [entry]
        for e in entries:
            if not isinstance(e, dict):
                continue
            usage = max(
                e.get("call_count", 0) or 0,
                e.get("total_cputime", 0) or 0,
                e.get("total_time", 0) or 0,
            )
            threshold = 90
            if usage >= threshold:
                wait = int(e.get("estimated_time_to_regain_access") or _DEFAULT_RETRY_AFTER)
                record_throttle(account_id, retry_after=wait)
                return
