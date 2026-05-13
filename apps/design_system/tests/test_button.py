from __future__ import annotations

import pytest

from apps.design_system.tests.conftest import cotton_render


@pytest.mark.parametrize(
    ("variant", "classes"),
    [
        ("primary", "bg-brand-600 text-white"),
        ("secondary", "bg-surface text-ink"),
        ("ghost", "bg-transparent"),
        ("danger", "bg-red-600 text-white"),
    ],
)
def test_button_variant_classes(variant: str, classes: str) -> None:
    rendered = cotton_render(f"<c-button variant='{variant}'>Go</c-button>")
    assert "Go" in rendered
    for cls in classes.split():
        assert cls in rendered


def test_button_default_is_primary() -> None:
    rendered = cotton_render("<c-button>OK</c-button>")
    assert "bg-brand-600" in rendered
