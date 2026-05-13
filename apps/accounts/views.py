from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def pending_approval(request: HttpRequest) -> HttpResponse:
    return render(request, "accounts/pending_approval.html")
