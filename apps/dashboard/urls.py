from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("clients/<slug:slug>/", views.client_detail, name="client-detail"),
    path("accounts/<str:account_id>/refresh/", views.refresh_account, name="refresh-account"),
    path("export.csv", views.export_csv, name="export-csv"),
]
