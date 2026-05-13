"""Production settings — Railway."""

from .base import *  # noqa: F403

DEBUG = False

# Security headers
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

# CSRF trusted origins (Railway)
import os  # noqa: E402

_railway = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
CSRF_TRUSTED_ORIGINS = [f"https://{_railway}"] if _railway else []
ALLOWED_HOSTS = [_railway] if _railway else []

# Sentry
import sentry_sdk  # noqa: E402
from sentry_sdk.integrations.celery import CeleryIntegration  # noqa: E402
from sentry_sdk.integrations.django import DjangoIntegration  # noqa: E402

if SENTRY_DSN := env("SENTRY_DSN", default=""):  # noqa: F405
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=env("RAILWAY_ENVIRONMENT", default="production"),  # noqa: F405
    )

# Structured JSON logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "apps.core.logging.JSONFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

if not CRYPTOGRAPHY_KEY:  # noqa: F405
    raise RuntimeError("FERNET_KEY env var must be set in production")
if not SECRET_KEY or SECRET_KEY.startswith("dev-"):  # noqa: F405
    raise RuntimeError("DJANGO_SECRET_KEY must be set to a real value in production")
