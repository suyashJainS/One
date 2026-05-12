from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import include, path


def root(request: HttpRequest) -> HttpResponse:
    return render(request, "base.html")


urlpatterns = [
    path("", root),
    path("admin/", admin.site.urls),
    path("auth/", include("allauth.urls")),
]
