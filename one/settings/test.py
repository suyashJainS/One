"""Test settings — used by pytest."""

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-insecure-key"  # noqa: S105
ALLOWED_HOSTS = ["*"]

DATABASES["default"].setdefault("TEST", {})["NAME"] = "test_one"  # noqa: F405

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Fixed key so encryption tests are deterministic
CRYPTOGRAPHY_KEY = "QbBn1q0KGE45w9P0gZk7w5b0u0H8H8H8H8H8H8H8H8E="

LOGGING = {"version": 1, "disable_existing_loggers": True, "handlers": {}, "root": {"handlers": []}}
