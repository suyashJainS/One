from django.contrib import admin
from django.http import HttpResponse
from django.urls import path


def root(_request):
    return HttpResponse("One — Performance Marketing Portal")


urlpatterns = [
    path("", root),
    path("admin/", admin.site.urls),
]
