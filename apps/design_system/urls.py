from __future__ import annotations

from django.urls import path

from .views import showroom

urlpatterns = [path("", showroom)]
