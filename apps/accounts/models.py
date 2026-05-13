from __future__ import annotations

from django.conf import settings
from django.db import models
from solo.models import SingletonModel


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    timezone = models.CharField(max_length=40, default="Asia/Kolkata")
    is_approved = models.BooleanField(default=False)
    # default_account: added in Phase G after clients.MetaAdAccount exists
    # default_account = models.ForeignKey(
    #     "clients.MetaAdAccount", on_delete=models.SET_NULL,
    #     null=True, blank=True, related_name="+",
    # )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Profile<{self.user.email or self.user.username}>"


class OwnerAllowlist(SingletonModel):
    emails = models.JSONField(default=list, blank=True)
    auto_approve = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Owner allowlist"

    @classmethod
    def is_owner(cls, email: str) -> bool:
        if not email:
            return False
        instance = cls.get_solo()
        if not instance.auto_approve:
            return False
        return email.lower() in (e.lower() for e in instance.emails)

    def __str__(self) -> str:
        return "Owner allowlist"
