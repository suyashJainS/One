"""Development settings — local machine."""

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = "dev-insecure-do-not-use-in-prod"  # noqa: S105
ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1"]

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)-8s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"django.db.backends": {"level": "WARNING"}},
}

# Dev FERNET_KEY (regenerate per developer if rotated)
import base64  # noqa: E402
import os  # noqa: E402

CRYPTOGRAPHY_KEY = CRYPTOGRAPHY_KEY or base64.urlsafe_b64encode(os.urandom(32)).decode()  # noqa: F405
