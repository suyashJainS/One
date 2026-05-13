from __future__ import annotations

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
