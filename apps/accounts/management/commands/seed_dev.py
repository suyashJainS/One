"""Seed a dev/test admin user (idempotent)."""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import OwnerAllowlist, UserProfile

User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        email = "smoke@example.com"
        password = "smoke-test-pass-123"  # noqa: S105
        user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
        user.set_password(password)
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_approved = True
        profile.save()
        al = OwnerAllowlist.get_solo()
        if email not in al.emails:
            al.emails = [*al.emails, email]
            al.auto_approve = True
            al.save()
        self.stdout.write(self.style.SUCCESS(f"Seeded {email} / {password}"))
