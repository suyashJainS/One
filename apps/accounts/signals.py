from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import OwnerAllowlist, UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender: type, instance: object, created: bool, **kwargs: object) -> None:
    if not created:
        return
    User = get_user_model()
    if not isinstance(instance, User):
        return
    is_owner = OwnerAllowlist.is_owner(instance.email or "")
    UserProfile.objects.get_or_create(
        user=instance,
        defaults={"is_approved": is_owner},
    )
