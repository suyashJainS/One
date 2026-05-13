from __future__ import annotations

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render


def showroom(request: HttpRequest) -> HttpResponse:
    if not settings.DEBUG:
        raise Http404
    return render(request, "design_system/showroom.html")
