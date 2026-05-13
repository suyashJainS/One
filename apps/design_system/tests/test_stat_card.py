from __future__ import annotations

from apps.design_system.tests.conftest import cotton_render


def test_stat_card_positive_delta_is_green() -> None:
    out = cotton_render(
        '<c-stat-card label="Spend" value="$24,180" delta="8.2" delta_direction="up" />'
    )
    assert "Spend" in out
    assert "$24,180" in out
    assert "8.2" in out
    assert "text-emerald-600" in out


def test_stat_card_negative_delta_is_red() -> None:
    out = cotton_render(
        '<c-stat-card label="Leads" value="1,240" delta="-4" delta_direction="down" />'
    )
    assert "text-red-600" in out
