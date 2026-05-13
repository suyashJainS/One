from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

WHITELIST_PREFIXES = ("/auth/", "/static/", "/healthz", "/admin/", "/robots.txt", "/metrics")


class ApprovalRequiredMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return self.get_response(request)
        if user.is_superuser:
            return self.get_response(request)
        if any(request.path.startswith(p) for p in WHITELIST_PREFIXES):
            return self.get_response(request)
        profile = getattr(user, "profile", None)
        if profile is not None and profile.is_approved:
            return self.get_response(request)
        return redirect("/auth/pending-approval/")
