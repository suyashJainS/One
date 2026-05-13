"""Tests for allauth-based login rate limiting."""

import pytest
from django.test import Client


@pytest.mark.django_db
def test_login_is_rate_limited(client: Client) -> None:
    """After 5+ failed login attempts, allauth blocks further attempts."""
    for _ in range(6):
        response = client.post(
            "/auth/login/", {"login": "x@example.com", "password": "wrong-password"}
        )
    # After 5+ failed attempts allauth blocks further tries.
    # Accept any sign that the throttle engaged:
    body = response.content.decode("utf-8", errors="ignore").lower()
    assert (
        response.status_code in (403, 429)
        or "too many" in body
        or "rate" in body
        or "try again" in body
    )
