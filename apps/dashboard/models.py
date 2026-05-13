from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any, ClassVar

from django.db import models

from apps.clients.models import MetaAdAccount


class DailyMetricsCache(models.Model):
    SOURCE_MANUAL = "manual"
    SOURCE_BEAT = "beat"

    account = models.ForeignKey(
        MetaAdAccount, on_delete=models.CASCADE, related_name="daily_metrics"
    )
    date = models.DateField()
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impressions = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    cpm = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    ctr = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    frequency = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    reach = models.BigIntegerField(default=0)
    outbound_clicks = models.BigIntegerField(default=0)
    outbound_clicks_ctr = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    landing_page_views = models.BigIntegerField(default=0)
    add_to_cart = models.BigIntegerField(default=0)
    purchases = models.BigIntegerField(default=0)
    purchase_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    leads = models.BigIntegerField(default=0)
    source = models.CharField(max_length=8, default=SOURCE_MANUAL)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints: ClassVar = [
            models.UniqueConstraint(fields=["account", "date"], name="uniq_account_date")
        ]
        indexes: ClassVar = [models.Index(fields=["account", "-date"])]
        ordering: ClassVar = ["-date", "account_id"]

    def __str__(self) -> str:
        return f"{self.account.account_id} {self.date}"

    @property
    def cost_per_purchase(self) -> Decimal | None:
        return (self.spend / self.purchases) if self.purchases else None

    @property
    def cost_per_lead(self) -> Decimal | None:
        return (self.spend / self.leads) if self.leads else None

    @property
    def roas(self) -> Decimal | None:
        return (self.purchase_value / self.spend) if self.spend else None

    @classmethod
    def upsert(cls, account: MetaAdAccount, date: dt.date, **fields: Any) -> DailyMetricsCache:
        defaults = {k: v for k, v in fields.items() if k != "source"}
        row, _ = cls.objects.update_or_create(
            account=account,
            date=date,
            defaults={**defaults, "source": fields.get("source", cls.SOURCE_MANUAL)},
        )
        return row
