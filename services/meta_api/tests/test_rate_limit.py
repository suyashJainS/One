from collections.abc import Generator

import pytest
from django.core.cache import cache

from services.meta_api.rate_limit import (
    cooldown_seconds,
    in_cooldown,
    record_throttle,
    record_usage,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> Generator[None, None, None]:
    cache.clear()
    yield
    cache.clear()


def test_no_cooldown_by_default() -> None:
    assert not in_cooldown("act_1")
    assert cooldown_seconds("act_1") == 0


def test_record_throttle_starts_cooldown() -> None:
    record_throttle("act_1", retry_after=30)
    assert in_cooldown("act_1")
    assert 0 < cooldown_seconds("act_1") <= 30


def test_record_usage_high_call_count_triggers_cooldown() -> None:
    headers_value = (
        '{"acc_id_1":{"call_count":95,"total_cputime":10,"total_time":10,'
        '"estimated_time_to_regain_access":30}}'
    )
    record_usage("act_1", headers_value)
    assert in_cooldown("act_1")
