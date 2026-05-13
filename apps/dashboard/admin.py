from django.contrib import admin

from .models import DailyMetricsCache


@admin.register(DailyMetricsCache)
class DailyMetricsCacheAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "date",
        "account",
        "spend",
        "purchases",
        "purchase_value",
        "leads",
        "source",
        "fetched_at",
    )
    list_filter = ("source", "account__client")
    search_fields = ("account__account_id", "account__account_name")
    date_hierarchy = "date"
