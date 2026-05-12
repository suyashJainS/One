"""Observability models — ActivityLog + APIRequestLog."""

from __future__ import annotations

from typing import Any, ClassVar

from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    class Level(models.TextChoices):
        INFO = "info", "Info"
        WARN = "warn", "Warning"
        ERROR = "error", "Error"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    level = models.CharField(max_length=8, choices=Level.choices, default=Level.INFO)
    action = models.CharField(max_length=80, blank=True)
    path = models.CharField(max_length=512)
    method = models.CharField(max_length=8)
    status_code = models.PositiveSmallIntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    request_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes: ClassVar = [models.Index(fields=["user", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.method} {self.path} -> {self.status_code}"


REDACTED_KEYS = frozenset(
    {
        "access_token",
        "fb_access_token",
        "appsecret_proof",
        "client_secret",
        "password",
        "authorization",
    }
)


def _redact(value: object) -> object:
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if k.lower() in REDACTED_KEYS else _redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


class APIRequestLog(models.Model):
    service = models.CharField(max_length=32)
    method = models.CharField(max_length=8)
    url = models.TextField()
    query_params = models.JSONField(default=dict, blank=True)
    request_body = models.JSONField(null=True, blank=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="api_request_logs",
    )
    # client FK added in Task G1 (clients app does not yet exist)
    # client = models.ForeignKey(
    #     "clients.Client", on_delete=models.SET_NULL, null=True, blank=True,
    #     related_name="api_request_logs",
    # )
    request_id = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes: ClassVar = [models.Index(fields=["service", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.service} {self.method} {self.status_code}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.query_params = _redact(self.query_params)
        self.request_body = _redact(self.request_body)
        super().save(*args, **kwargs)
