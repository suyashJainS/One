"""Tests for the sentry_test management command."""

import pytest
from django.core.management import call_command


def test_sentry_test_command_raises() -> None:
    with pytest.raises(RuntimeError, match="sentry-test"):
        call_command("sentry_test")
