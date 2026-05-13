"""Tests that prod settings refuse to start without required env vars."""

import importlib
import sys

import pytest


def _clean_settings_modules() -> None:
    for key in list(sys.modules.keys()):
        if key.startswith("one.settings"):
            sys.modules.pop(key, None)


def test_prod_requires_fernet_key(monkeypatch) -> None:
    # Clean any cached prod settings module so it re-evaluates
    _clean_settings_modules()
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "one.settings.prod")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "real-secret-key-with-enough-entropy-123456789")
    monkeypatch.setenv("DATABASE_URL", "postgres://x:y@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.delenv("FERNET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="FERNET_KEY"):
        importlib.import_module("one.settings.prod")
    _clean_settings_modules()


def test_prod_requires_real_secret_key(monkeypatch) -> None:
    _clean_settings_modules()
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "one.settings.prod")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "dev-insecure")
    monkeypatch.setenv("FERNET_KEY", "QbBn1q0KGE45w9P0gZk7w5b0u0H8H8H8H8H8H8H8H8E=")
    monkeypatch.setenv("DATABASE_URL", "postgres://x:y@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    with pytest.raises(RuntimeError, match="DJANGO_SECRET_KEY"):
        importlib.import_module("one.settings.prod")
    _clean_settings_modules()
