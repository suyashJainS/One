from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.test import Client as DjangoClient

from apps.clients.models import Client, ClientMetaCredentials, MetaAdAccount
from apps.dashboard.models import DailyMetricsCache

User = get_user_model()


@pytest.fixture
def approved_user(db: None) -> Any:
    u = User.objects.create_user(username="u@x", email="u@x", password="x" * 14)
    u.profile.is_approved = True  # type: ignore[attr-defined]
    u.profile.save()  # type: ignore[attr-defined]
    return u


@pytest.fixture
def seeded(db: None) -> tuple[Client, MetaAdAccount]:
    c = Client.objects.create(name="Acme", slug="acme", target_roas=Decimal("3"))
    a = MetaAdAccount.objects.create(client=c, account_id="act_1", currency="USD")
    today = dt.date.today()
    yesterday = today - dt.timedelta(days=1)
    DailyMetricsCache.objects.create(
        account=a,
        date=today,
        spend=Decimal("1000"),
        purchases=10,
        purchase_value=Decimal("3000"),
        leads=20,
        impressions=10000,
        clicks=500,
    )
    DailyMetricsCache.objects.create(
        account=a,
        date=yesterday,
        spend=Decimal("800"),
        purchases=8,
        purchase_value=Decimal("2400"),
        leads=18,
        impressions=8000,
        clicks=420,
    )
    return c, a


@pytest.mark.django_db
def test_overview_requires_login(client: DjangoClient) -> None:
    response = client.get("/dashboard/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_overview_renders_kpis_and_row(
    client: DjangoClient,
    approved_user: Any,
    seeded: tuple[Client, MetaAdAccount],
) -> None:
    client.force_login(approved_user)
    response = client.get("/dashboard/")
    assert response.status_code == 200
    assert b"Acme" in response.content
    # Today spend KPI present
    assert b"1,000" in response.content or b"1000" in response.content
    # ROAS = 3000/1000 = 3.00
    assert b"3.0" in response.content


@pytest.mark.django_db
def test_overview_handles_no_data(
    client: DjangoClient,
    approved_user: Any,
) -> None:
    client.force_login(approved_user)
    response = client.get("/dashboard/")
    assert response.status_code == 200
    assert b"No clients yet" in response.content or b"No data" in response.content


@pytest.mark.django_db
def test_refresh_account_handles_auth_error_gracefully(
    client: DjangoClient, approved_user: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    c = Client.objects.create(name="Acme", slug="acme")
    ClientMetaCredentials.objects.create(client=c, access_token="bad")
    account = MetaAdAccount.objects.create(client=c, account_id="act_99", currency="USD")

    from services.meta_api.errors import AuthError

    def fake_pull(**kwargs: Any) -> None:
        raise AuthError(status_code=401, code=190, message="Invalid OAuth token")

    monkeypatch.setattr("apps.dashboard.views.pull_account_metrics_sync", fake_pull)

    client.force_login(approved_user)
    response = client.post(
        f"/dashboard/accounts/{account.account_id}/refresh/",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code in (200, 502)
    assert b"Auth error" in response.content
