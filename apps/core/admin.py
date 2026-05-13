from django.contrib import admin

from .models import ActivityLog, APIRequestLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("created_at", "method", "path", "status_code", "user", "duration_ms")
    list_filter = ("level", "method", "status_code")
    search_fields = ("path", "request_id", "user__email")
    readonly_fields = tuple(f.name for f in ActivityLog._meta.fields)


@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("created_at", "service", "method", "status_code", "duration_ms")
    list_filter = ("service", "method", "status_code")
    search_fields = ("url", "request_id")
    readonly_fields = tuple(f.name for f in APIRequestLog._meta.fields)
