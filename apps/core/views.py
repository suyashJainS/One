"""Core views — healthz endpoint."""

from __future__ import annotations

from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest, JsonResponse


def healthz(_request: HttpRequest) -> JsonResponse:
    db_ok = True
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception:
        db_ok = False

    cache_ok = True
    try:
        cache.set("__healthz__", "1", 5)
        cache_ok = cache.get("__healthz__") == "1"
    except Exception:
        cache_ok = False

    status = "ok" if db_ok and cache_ok else "degraded"
    code = 200 if status == "ok" else 503
    return JsonResponse(
        {"status": status, "db": "ok" if db_ok else "down", "cache": "ok" if cache_ok else "down"},
        status=code,
    )
