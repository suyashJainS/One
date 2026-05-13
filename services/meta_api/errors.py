"""Meta API error taxonomy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MetaAPIError(Exception):
    status_code: int
    code: int | None = None
    subcode: int | None = None
    message: str = ""
    body: Any = None

    def __str__(self) -> str:
        return f"[{self.status_code}/{self.code}] {self.message}"


class AuthError(MetaAPIError):
    """Token invalid / expired / lacks permission."""


class RateLimitError(MetaAPIError):
    """Throttled by Meta. Retry after backoff."""

    retry_after_seconds: int = 60


class InvalidParamError(MetaAPIError):
    """Bad request — do not retry without fixing input."""


class TransientError(MetaAPIError):
    """5xx / network — safe to retry."""


class FatalError(MetaAPIError):
    """Anything else — fail loudly."""


# Codes from https://developers.facebook.com/docs/marketing-api/error-reference
_AUTH_CODES = {190, 102, 200, 459, 463, 467}
_RATE_LIMIT_CODES = frozenset({4, 17, 32, 613, *range(80000, 80009)})
_INVALID_CODES = {100, 110, 803}

_HTTP_UNAUTHORIZED = 401
_HTTP_SERVER_ERROR_THRESHOLD = 500


def classify(status_code: int, body: dict[str, Any]) -> MetaAPIError:
    raw_error = body.get("error", {}) if isinstance(body, dict) else {}
    error = raw_error if isinstance(raw_error, dict) else {}
    code = error.get("code")
    subcode = error.get("error_subcode")
    message = error.get("message", "")
    common = {
        "status_code": status_code,
        "code": code,
        "subcode": subcode,
        "message": message,
        "body": body,
    }

    if status_code == _HTTP_UNAUTHORIZED or code in _AUTH_CODES:
        return AuthError(**common)
    if code in _RATE_LIMIT_CODES:
        err = RateLimitError(**common)
        # Meta hints retry-after via headers; populated at call site.
        return err
    if code in _INVALID_CODES:
        return InvalidParamError(**common)
    if status_code >= _HTTP_SERVER_ERROR_THRESHOLD:
        return TransientError(**common)
    return FatalError(**common)
