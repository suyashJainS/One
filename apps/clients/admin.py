from __future__ import annotations

from django.contrib import admin

from .models import Client, ClientMetaCredentials, MetaAdAccount


class CredentialsInline(admin.StackedInline):  # type: ignore[type-arg]
    model = ClientMetaCredentials
    fields = ("api_version", "last_validated_at")  # don't display tokens
    readonly_fields = ("last_validated_at",)


class AdAccountInline(admin.TabularInline):  # type: ignore[type-arg]
    model = MetaAdAccount
    extra = 0
    fields = ("account_id", "account_name", "currency", "is_active", "last_sync_at")
    readonly_fields = ("last_sync_at",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("name", "slug", "is_active", "target_roas", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}  # noqa: RUF012
    inlines = [CredentialsInline, AdAccountInline]  # noqa: RUF012


@admin.register(MetaAdAccount)
class MetaAdAccountAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("account_id", "account_name", "client", "is_active", "last_sync_at")
    list_filter = ("is_active", "client")
    search_fields = ("account_id", "account_name")
