"""Meta Graph API HTTP client with retries, logging, and error translation."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from django.conf import settings

from apps.clients.models import MetaAdAccount
from apps.core.models import APIRequestLog

from .errors import RateLimitError, TransientError, classify
from .rate_limit import cooldown_seconds, in_cooldown, record_throttle, record_usage
from .tokens import resolve_token

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.facebook.com"


def _build_url(api_version: str, account_id: str, path: str) -> str:
    """Construct the full Graph API URL.

    - path="/" or path=""       → https://graph.facebook.com/v22.0/act_1
    - path="insights"           → https://graph.facebook.com/v22.0/act_1/insights
    - path="/insights"          → https://graph.facebook.com/v22.0/act_1/insights
    - path containing account_id already → don't double it
    """
    # Normalise: strip leading slash, strip empty
    clean = path.lstrip("/").rstrip("/")

    if f"/{account_id}" in path:
        # Caller already included the account ID in path (with leading slash)
        return f"{GRAPH_BASE}/{api_version}/{clean}"

    if clean.startswith(f"{account_id}/") or clean == account_id:
        # Caller passed account_id without leading slash, e.g. "act_1/insights"
        return f"{GRAPH_BASE}/{api_version}/{clean}"

    if not clean:
        return f"{GRAPH_BASE}/{api_version}/{account_id}"

    return f"{GRAPH_BASE}/{api_version}/{account_id}/{clean}"


class MetaAPIClient:
    def __init__(
        self,
        timeout_seconds: float = 15.0,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
        api_version: str | None = None,
    ) -> None:
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.backoff = retry_backoff_seconds
        self.api_version: str = api_version or settings.META_API_VERSION
        self._http = httpx.Client(timeout=self.timeout)

    def get(self, account: MetaAdAccount, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", account, path, params=params or {})

    def post(self, account: MetaAdAccount, path: str, data: dict[str, Any] | None = None) -> Any:
        return self._request("POST", account, path, data=data or {})

    def _request(
        self,
        method: str,
        account: MetaAdAccount,
        path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        if in_cooldown(account.account_id):
            wait = cooldown_seconds(account.account_id)
            raise RateLimitError(
                status_code=429,
                code=None,
                message=f"In cooldown for {wait}s",
            )

        token = resolve_token(account)
        url = _build_url(self.api_version, account.account_id, path)

        request_params = dict(params or {})
        request_params["access_token"] = token

        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.monotonic()
            try:
                if method == "GET":
                    response = self._http.get(url, params=request_params)
                else:
                    response = self._http.post(url, params={"access_token": token}, data=data or {})
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_err = exc
                self._log(
                    account,
                    method,
                    url,
                    request_params,
                    data,
                    None,
                    None,
                    int((time.monotonic() - started) * 1000),
                    repr(exc),
                )
                if attempt < self.max_retries:
                    time.sleep(self.backoff * (2**attempt))
                    continue
                raise

            duration_ms = int((time.monotonic() - started) * 1000)
            try:
                body = response.json()
            except ValueError:
                body = None

            self._log(
                account,
                method,
                url,
                request_params,
                data,
                response.status_code,
                body,
                duration_ms,
                "",
            )
            record_usage(
                account.account_id,
                response.headers.get("X-Business-Use-Case-Usage")
                or response.headers.get("X-Ad-Account-Usage"),
            )

            if response.is_success:
                return body

            err = classify(response.status_code, body or {})

            if isinstance(err, RateLimitError):
                retry_after = int(response.headers.get("Retry-After") or 60)
                err.retry_after_seconds = retry_after
                record_throttle(account.account_id, retry_after=retry_after)
                raise err

            if isinstance(err, TransientError) and attempt < self.max_retries:
                last_err = err
                time.sleep(self.backoff * (2**attempt))
                continue

            raise err

        # Exhausted retries on transient
        if last_err:
            raise last_err
        raise RuntimeError("unreachable")  # pragma: no cover

    def _log(
        self,
        account: MetaAdAccount,
        method: str,
        url: str,
        params: dict[str, Any],
        body: dict[str, Any] | None,
        status: int | None,
        response_body: Any,
        duration_ms: int,
        error: str,
    ) -> None:
        try:
            APIRequestLog.objects.create(
                service="meta_api",
                method=method,
                url=url,
                query_params=params,
                request_body=body,
                status_code=status,
                response_body=response_body if isinstance(response_body, dict | list) else None,
                duration_ms=duration_ms,
                error=error,
                client=account.client,
            )
        except Exception:
            logger.exception("APIRequestLog write failed")
