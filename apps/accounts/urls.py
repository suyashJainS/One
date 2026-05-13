from __future__ import annotations

from django.urls import path

from .views import pending_approval

urlpatterns = [
    path("pending-approval/", pending_approval, name="pending-approval"),
]
