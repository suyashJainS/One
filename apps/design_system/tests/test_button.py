from __future__ import annotations

import pytest
from django.template import Context, engines
from django.template.backends.django import DjangoTemplates
from django_cotton.compiler_regex import CottonCompiler


def cotton_render(src: str, ctx: dict[str, object] | None = None) -> str:
    """Render a cotton template string through the full cotton compiler pipeline."""
    compiler = CottonCompiler()
    compiled: str = compiler.process(src)
    eng: DjangoTemplates = engines["django"]  # type: ignore[assignment]
    cached_loader = eng.engine.template_loaders[0]
    cotton_loader = cached_loader.loaders[0]  # type: ignore[attr-defined]
    t = cotton_loader.get_template_from_string(compiled)
    return str(t.render(Context(ctx or {})))


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
