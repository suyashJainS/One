# apps/core/tests/test_logging.py
import json
import logging

from apps.core.logging import JSONFormatter


def test_json_formatter_emits_valid_json() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x",
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    out = JSONFormatter().format(record)
    parsed = json.loads(out)
    assert parsed["message"] == "hello world"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test"
