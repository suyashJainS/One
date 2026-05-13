from __future__ import annotations

from django import template

register = template.Library()


@register.filter
def split(value: str, delim: str = ",") -> list[str]:
    return [v.strip() for v in str(value).split(delim) if v.strip()]
