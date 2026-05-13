"""Tests for Content-Security-Policy headers."""

import pytest
from django.test import Client


@pytest.mark.django_db
def test_csp_header_present(client: Client) -> None:
    response = client.get("/")
    csp = response.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
