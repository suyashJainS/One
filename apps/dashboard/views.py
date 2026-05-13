from __future__ import annotations

import csv
import datetime as dt

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.clients.models import Client, MetaAdAccount

from .models import DailyMetricsCache
from .services import ClientSummary, overview_data
from .tasks import pull_account_metrics_sync


@login_required
def overview(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard/overview.html", overview_data())


@login_required
def client_detail(request: HttpRequest, slug: str) -> HttpResponse:
    client = get_object_or_404(Client, slug=slug, is_active=True)
    today = timezone.localdate()
    since = request.GET.get("since") or (today - dt.timedelta(days=29)).isoformat()
    until = request.GET.get("until") or today.isoformat()
    rows = (
        DailyMetricsCache.objects.filter(account__client=client, date__range=[since, until])
        .select_related("account")
        .order_by("-date", "account__account_name")
    )
    chart_labels = [r.date.isoformat() for r in rows]
    chart_spend = [float(r.spend) for r in rows]
    chart_roas = [float(r.roas or 0) for r in rows]
    return render(
        request,
        "dashboard/client_detail.html",
        {
            "client": client,
            "since": since,
            "until": until,
            "rows": rows,
            "chart_labels": chart_labels,
            "chart_spend": chart_spend,
            "chart_roas": chart_roas,
        },
    )


@login_required
@require_http_methods(["POST"])
def refresh_account(request: HttpRequest, account_id: str) -> HttpResponse:
    account = get_object_or_404(MetaAdAccount, account_id=account_id, is_active=True)
    date_str = request.POST.get("date") or timezone.localdate().isoformat()
    pull_account_metrics_sync(account_id=account.account_id, date=date_str)
    if getattr(request, "htmx", False):
        return render(
            request,
            "dashboard/_client_row.html",
            {"summary": _single_client_summary(account.client)},
        )
    return HttpResponse("ok")


def _single_client_summary(client: Client) -> ClientSummary | None:
    from typing import cast

    clients = cast(list[ClientSummary], overview_data()["clients"])
    for s in clients:
        if s.client_id == client.id:
            return s
    return None


@login_required
def export_csv(request: HttpRequest) -> HttpResponse:
    today = timezone.localdate()
    since_str = request.GET.get("since") or (today - dt.timedelta(days=29)).isoformat()
    until_str = request.GET.get("until") or today.isoformat()
    rows = (
        DailyMetricsCache.objects.filter(date__range=[since_str, until_str])
        .select_related("account__client")
        .order_by("date", "account__account_id")
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="metrics-{since_str}-to-{until_str}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(
        [
            "date",
            "client",
            "account_id",
            "account_name",
            "spend",
            "impressions",
            "clicks",
            "purchases",
            "purchase_value",
            "leads",
            "roas",
            "cpl",
            "cpp",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.date,
                r.account.client.name,
                r.account.account_id,
                r.account.account_name,
                r.spend,
                r.impressions,
                r.clicks,
                r.purchases,
                r.purchase_value,
                r.leads,
                r.roas or "",
                r.cost_per_lead or "",
                r.cost_per_purchase or "",
            ]
        )
    return response
