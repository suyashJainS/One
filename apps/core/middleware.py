"""Core middleware — RequestIDMiddleware, NoIndexMiddleware, ActivityLogMiddleware."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    HEADER = "X-Request-ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming = (request.headers.get(self.HEADER) or "")[:64]
        request_id = incoming or str(uuid.uuid4())
        request.request_id = request_id  # type: ignore[attr-defined]
        response = self.get_response(request)
        response[self.HEADER] = request_id
        return response


class NoIndexMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response


SKIP_PATHS = ("/static/", "/healthz", "/metrics", "/admin/jsi18n/")

_HTTP_CLIENT_ERROR_THRESHOLD = 400
_HTTP_SERVER_ERROR_THRESHOLD = 500


class ActivityLogMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if any(request.path.startswith(p) for p in SKIP_PATHS):
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        # Import lazily to avoid AppRegistryNotReady at import time
        from apps.core.models import ActivityLog

        if response.status_code < _HTTP_CLIENT_ERROR_THRESHOLD:
            level = "info"
        elif response.status_code < _HTTP_SERVER_ERROR_THRESHOLD:
            level = "warn"
        else:
            level = "error"

        try:
            ActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                level=level,
                path=request.path[:512],
                method=request.method or "",
                status_code=response.status_code,
                ip_address=_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
                duration_ms=duration_ms,
                request_id=getattr(request, "request_id", "")[:64],
            )
        except Exception:
            logger.exception("ActivityLog write failed")
        return response


def _client_ip(request: HttpRequest) -> str | None:
    forwarded: str = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",", maxsplit=1)[0].strip()
    remote: str = request.META.get("REMOTE_ADDR", "")
    return remote or None
