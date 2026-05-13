# ADR 003 — django-cotton for template components

Date: 2026-05-13
Status: Accepted

## Context

Django's built-in template language is fine for pages but awkward for reusable UI components. The standard pattern — `{% include "components/card.html" with title=x body=y %}` — doesn't support named slots, and the `with` clause is verbose. This becomes painful when building a design system with 10–20 components that accept different combinations of content.

Options considered:

- **Plain `{% include %}` with `{% with %}`**: Works, but no slot mechanism. Components that need a header slot, a body slot, and an optional footer become deeply nested includes or require duplicated template code.
- **django-components**: Slot support, Python-defined component classes. More powerful but heavier — each component needs a Python class alongside its template.
- **django-cotton**: Slot/prop syntax using custom HTML-like tags (`<c-card title="foo"><c-slot:body>...</c-slot:body></c-card>`). No Python class required per component. The template IS the component definition. Similar ergonomics to JSX or Svelte slots, implemented as a Django template tag preprocessor.
- **Jinja2 + macros**: Macros give component-like composition. Would require switching Django's template backend; breaks `{% url %}`, `{% csrf_token %}`, and other Django-specific tags.

## Decision

Use `django-cotton` for all reusable UI components. Components live in `templates/cotton/` and are invoked as `<c-component-name prop="value">` in any template. The cotton preprocessor runs as part of the Django template loader chain.

## Consequences

**Positive:**
- Clean component definitions: a single HTML file with `{{ slot }}` and `{{ prop }}` variables.
- No Python boilerplate per component. Adding a new component is adding a file.
- Template inheritance and `{% include %}` still work alongside cotton components; you can mix both.
- The design system showroom (`/design-system/`) renders every component in isolation.

**Negative:**
- One extra dependency. If `django-cotton` is abandoned or breaks on a future Django version, templates need rewriting.
- Unit-testing cotton components requires a workaround: the `<c-*>` tags are transformed at render time by cotton's template loader, so standard Django `render_to_string` in tests sees the raw (untransformed) HTML if the test settings don't include the cotton loader. The project conftest configures the template engine to include cotton's loader, which resolves this but is a non-obvious setup step for new contributors.
- IDEs and linters treat `<c-*>` as unknown HTML elements. HTML validators will flag them. This is cosmetic but slightly annoying.

The component ergonomics win clearly over the alternatives at this scale. The testing workaround is documented in `conftest.py`.
