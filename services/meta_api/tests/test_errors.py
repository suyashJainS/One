from services.meta_api.errors import (
    AuthError,
    FatalError,
    InvalidParamError,
    MetaAPIError,
    RateLimitError,
    TransientError,
    classify,
)


def test_hierarchy() -> None:
    for cls in (AuthError, FatalError, InvalidParamError, RateLimitError, TransientError):
        assert issubclass(cls, MetaAPIError)


def test_classify_401() -> None:
    err = classify(401, {"error": {"code": 190, "message": "Invalid token"}})
    assert isinstance(err, AuthError)


def test_classify_4_rate_limit() -> None:
    err = classify(400, {"error": {"code": 4, "message": "Application request limit reached"}})
    assert isinstance(err, RateLimitError)


def test_classify_17_user_rate_limit() -> None:
    err = classify(400, {"error": {"code": 17, "message": "User request limit reached"}})
    assert isinstance(err, RateLimitError)


def test_classify_100_invalid_param() -> None:
    err = classify(400, {"error": {"code": 100, "message": "Invalid parameter"}})
    assert isinstance(err, InvalidParamError)


def test_classify_500_transient() -> None:
    err = classify(503, {})
    assert isinstance(err, TransientError)


def test_classify_unknown_becomes_fatal() -> None:
    err = classify(400, {"error": {"code": 9999, "message": "Mystery"}})
    assert isinstance(err, FatalError)
