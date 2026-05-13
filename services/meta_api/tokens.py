"""Cascading token resolution for Meta API calls."""

from __future__ import annotations

from django.conf import settings

from apps.clients.models import MetaAdAccount


class TokenNotFound(Exception):
    pass


def resolve_token(account: MetaAdAccount) -> str:
    """Return the best available Meta access token for this account.

    Priority:
      1. ClientMetaCredentials.access_token (per-client)
      2. settings.META_FALLBACK_TOKEN (global env fallback)
    """
    creds = getattr(account.client, "credentials", None)
    if creds and creds.access_token:
        return str(creds.access_token)
    fallback: str = getattr(settings, "META_FALLBACK_TOKEN", "")
    if fallback:
        return fallback
    raise TokenNotFound(
        f"No Meta access token configured for account={account.account_id} "
        f"client={account.client.slug}"
    )
