from __future__ import annotations

from apps.design_system.tests.conftest import cotton_render


def test_card_renders_with_padding_and_shadow() -> None:
    out = cotton_render("<c-card>hello</c-card>")
    assert "hello" in out
    assert "stripe-card" in out
    assert "p-4" in out or "p-6" in out


def test_page_header_renders_title_and_subtitle() -> None:
    out = cotton_render('<c-page-header title="Dashboard" subtitle="Today" />')
    assert "Dashboard" in out
    assert "Today" in out


def test_empty_state_renders_title_and_description() -> None:
    out = cotton_render(
        '<c-empty-state title="No data" description="Add a client to get started" />'
    )
    assert "No data" in out
    assert "Add a client" in out


def test_skeleton_has_animated_class() -> None:
    out = cotton_render("<c-skeleton />")
    assert "animate-pulse" in out
