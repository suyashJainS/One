from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import migrations


def install(apps: object, schema_editor: object) -> None:
    Site = apps.get_model("sites", "Site")  # type: ignore[attr-defined]
    SocialApp = apps.get_model("socialaccount", "SocialApp")  # type: ignore[attr-defined]
    site, _ = Site.objects.get_or_create(pk=1, defaults={"domain": "localhost", "name": "One"})
    cid = getattr(settings, "FACEBOOK_OAUTH_CLIENT_ID", "") or ""
    sec = getattr(settings, "FACEBOOK_OAUTH_CLIENT_SECRET", "") or ""
    if not cid:
        return
    app, _ = SocialApp.objects.get_or_create(
        provider="facebook",
        name="Meta",
        defaults={"client_id": cid, "secret": sec},
    )
    app.client_id = cid
    app.secret = sec
    app.save()
    app.sites.add(site)


class Migration(migrations.Migration):
    dependencies: ClassVar = [
        ("accounts", "0002_seed_owner_allowlist"),
        ("sites", "0002_alter_domain_unique"),
        ("socialaccount", "0006_alter_socialaccount_extra_data"),
    ]
    operations: ClassVar = [migrations.RunPython(install, reverse_code=migrations.RunPython.noop)]
