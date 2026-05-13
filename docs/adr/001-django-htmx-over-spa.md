# ADR 001 — Django + HTMX over SPA

Date: 2026-05-13
Status: Accepted

## Context

One is a data-heavy admin portal for a single operator (or a small team) managing Meta Ads. The UI is table-heavy with filters, inline edits, and drill-downs — the kind of thing that looks like it calls for a React SPA but functionally doesn't need one.

Alternatives considered:

- **Inertia.js + React**: Keeps server-side routing, adds React components. Requires TypeScript, a separate React build pipeline, and prop serialization boilerplate. Two languages to debug.
- **React SPA + DRF**: Full separation. Adds a REST API layer, serializers, auth tokens, and a completely separate frontend codebase. Significant ongoing overhead for a solo operator.
- **Django + HTMX + Alpine + Cotton**: Server renders everything. HTMX handles partial page updates (filters, modal loads, form submissions without full reloads). Alpine.js handles small isolated client-side widgets. Cotton provides JSX-like component ergonomics in Django templates.

There is no deadline pressure. The priority is a system that is easy to maintain and extend over multiple cycles without accumulating frontend debt.

## Decision

Use server-rendered Django templates with HTMX for partial updates, Alpine.js for stateful widgets (dropdowns, date pickers, small interactive components), and django-cotton for reusable template components. Vite builds the JS and CSS bundle; HTMX, Alpine, and ApexCharts are bundled via npm.

## Consequences

**Positive:**
- Single language (Python) for all business logic. One process to debug, one test suite, one deployment artifact.
- Iteration speed is high: changing a table layout means editing a Django template, not refactoring a React component tree.
- No API layer to maintain. Data goes from ORM to template context directly.
- Full Django ORM, middleware, and form validation without adaptation layers.

**Negative:**
- Complex client state — drag-and-drop reordering, image editing, inline spreadsheet-style cells — will require heavier Alpine modules. Acceptable for Cycle 1's scope; revisit if a feature genuinely demands it.
- No mobile app for free. If One ever needs a native app or a machine-readable API, we'd need to expose a thin REST/JSON layer for those specific endpoints.
- HTMX swap patterns require care around CSS transitions and scroll position. Not hard, but less automatic than a virtual DOM.

The trade-off is appropriate for the current scale and team size.
