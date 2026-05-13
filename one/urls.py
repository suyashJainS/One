from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import include, path
from django.views.generic import TemplateView

from apps.core.views import healthz


def root(request: HttpRequest) -> HttpResponse:
    return render(request, "base.html")


urlpatterns = [
    path("", root),
    path("healthz", healthz),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("admin/", admin.site.urls),
    path("auth/", include("apps.accounts.urls")),
    path("auth/", include("allauth.urls")),
    path("design-system/", include("apps.design_system.urls")),
    path("clients/", include("apps.clients.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
]
