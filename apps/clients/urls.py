from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="list"),
    path("new/", views.client_new, name="new"),
    path("<slug:slug>/edit/", views.client_edit, name="edit"),
    path("<slug:slug>/delete/", views.client_delete, name="delete"),
]
