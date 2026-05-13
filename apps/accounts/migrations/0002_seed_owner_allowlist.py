from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import migrations


def seed(apps: object, schema_editor: object) -> None:
    OwnerAllowlist = apps.get_model("accounts", "OwnerAllowlist")  # type: ignore[attr-defined]
    instance, _ = OwnerAllowlist.objects.get_or_create(pk=1)
    if not instance.emails:
        instance.emails = [e.strip() for e in settings.OWNER_EMAILS if e.strip()]
        instance.save()


class Migration(migrations.Migration):
    dependencies: ClassVar = [("accounts", "0001_initial")]
    operations: ClassVar = [migrations.RunPython(seed, reverse_code=migrations.RunPython.noop)]
