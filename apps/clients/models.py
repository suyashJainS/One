from __future__ import annotations

from typing import ClassVar

from django.db import models

from apps.clients.fields import encrypt


class Client(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    target_roas = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    target_cpl = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    target_cpa = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    min_test_spend = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar = ["name"]

    def __str__(self) -> str:
        return self.name


class ClientMetaCredentials(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="credentials")
    access_token = encrypt(models.TextField(blank=True))
    fallback_token = encrypt(models.TextField(blank=True))
    api_version = models.CharField(max_length=8, default="v22.0")
    last_validated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"creds<{self.client.slug}>"


class MetaAdAccount(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="accounts")
    account_id = models.CharField(max_length=40, unique=True)  # 'act_<id>'
    account_name = models.CharField(max_length=120, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    timezone_offset = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar = ["account_name", "account_id"]
        indexes: ClassVar = [models.Index(fields=["client", "is_active"])]

    def __str__(self) -> str:
        return f"{self.account_name or self.account_id}"
