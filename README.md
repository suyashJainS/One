# One — Performance Marketing Portal

Django 5.2 portal for Meta Ads management. Cycle 1 ships foundation, auth, and a read-only dashboard. The stack is intentionally narrow: server-rendered templates, a single Python process for the web layer, and Celery for background work. No frontend framework, no separate API — the goal is a deployable, maintainable system one person can reason about entirely.

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Framework | Django 5.2 |
| Database | Postgres 16 |
| Cache / broker | Redis 7 |
| Background tasks | Celery 5 + Celery Beat |
| Frontend interactivity | HTMX 2 + Alpine.js 3 |
| CSS | Tailwind CSS 3 |
| Charts | ApexCharts 3 |
| Components | django-cotton |
| Build | Vite 5 |
| Deploy | Railway |

## Prerequisites

- **Docker** and **Docker Compose** (for Postgres + Redis in dev)
- **[uv](https://docs.astral.sh/uv/)** — Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Node 22+** — for the Vite/Tailwind build

## Quickstart — 5 minutes

```bash
# 1. Start backing services (Postgres + Redis)
docker compose up -d

# 2. Install Python deps
uv sync

# 3. Build frontend assets (CSS + JS bundle)
cd frontend && npm install && npm run build && cd ..

# 4. Configure environment
cp .env.example .env
# Minimum edit: set FERNET_KEY (see .env.example for the one-liner generator)
# Leave META_* and FACEBOOK_OAUTH_* empty for local dev without live API calls

# 5. Run migrations and seed dev data
uv run python manage.py migrate
uv run python manage.py seed_dev

# 6. Start the dev server
uv run python manage.py runserver
# → http://localhost:8000
```

Log in at http://localhost:8000/accounts/login/ with the seeded dev credentials (see below).

### Gotchas

**Port 5432 already in use.** If you have a local Postgres instance running on 5432, the Docker container will fail to bind that port. Either stop the local instance, or change the port mapping in `docker-compose.yml` (e.g., `"5433:5432"`) and update `DATABASE_URL` in `.env` accordingly. Both the Docker container and a local install use user=`one` password=`one` database=`one`.

**FERNET_KEY.** If `.env` has an empty `FERNET_KEY`, the app falls back to a key derived from `SECRET_KEY`. This is safe for local dev. In production, always set `FERNET_KEY` explicitly — losing it means losing all stored Meta access tokens. Generate one with:

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Frontend not rebuilding.** If you edit a template and the Tailwind class you added has no styling, it's because the class isn't in the built CSS. Run `npm run dev` (watch mode) in a separate terminal to pick up new classes during development.

## Running all services

In practice you need four processes. Run each in a separate terminal:

```bash
# Terminal 1 — Django dev server
uv run python manage.py runserver

# Terminal 2 — Celery worker (handles background Meta API jobs)
uv run celery -A one worker -l info

# Terminal 3 — Celery Beat scheduler (nightly ingestion tasks)
uv run celery -A one beat -l info

# Terminal 4 — Vite watch (rebuilds CSS + JS on file changes)
cd frontend && npm run dev
```

For a read-only walkthrough of the dashboard you only need Terminal 1.

## Tests

```bash
# All unit + integration tests (99 tests, ~10 seconds with --reuse-db)
uv run pytest

# With coverage report
uv run pytest --cov

# Playwright end-to-end smoke tests (requires dev server running on port 8000)
cd frontend && npx playwright test
```

The test suite requires no external services — Postgres and Redis connections are mocked or use the test settings (`one/settings/test.py`). The `--reuse-db` flag (set in `pyproject.toml`) skips re-migration on subsequent runs; run `uv run pytest --create-db` after a schema change.

## Demo credentials

The `seed_dev` management command creates a pre-approved owner account for local testing:

```
Email:    smoke@example.com
Password: smoke-test-pass-123
```

**These credentials are for local development only.** They are never seeded on Railway deployments. Do not use `smoke-test-pass-123` as a real password anywhere.

## Deploy

Deployments target Railway. Pushing to `main` triggers `.github/workflows/deploy.yml`.

Three Railway services share the same project:
- **web** — Gunicorn/Uvicorn (`gunicorn one.wsgi`)
- **worker** — Celery worker (`celery -A one worker -l info --concurrency=2`)
- **beat** — Celery Beat (`celery -A one beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`)

All three services share the same set of environment variables. Required vars are documented in `.env.example`. For full deploy instructions see `deploy/README.md`.

## Documentation

```
docs/
  superpowers/
    specs/      — Design specs (Cycle 1 and forward)
    plans/      — Implementation plans (per-cycle)
  adr/          — Architecture Decision Records
  runbooks/     — Operations procedures
deploy/
  README.md     — Railway-specific deploy notes
```

| Document | Purpose |
|---|---|
| `docs/adr/001-django-htmx-over-spa.md` | Why Django + HTMX instead of a SPA |
| `docs/adr/002-uv-over-pip-tools.md` | Why uv for dependency management |
| `docs/adr/003-cotton-for-templates.md` | Why django-cotton for components |
| `docs/adr/004-field-level-encryption.md` | Why custom Fernet field, not django-cryptography |
| `docs/adr/005-railway-deploy.md` | Why Railway as the deployment target |
| `docs/runbooks/db-restore.md` | Restore from a Railway Postgres snapshot |
| `docs/runbooks/fernet-key-rotation.md` | Rotate the FERNET_KEY without losing tokens |

## What is not in Cycle 1

- Write operations via Meta API (Cycle 2)
- Mobile app or REST API
- Multi-tenant or white-label support
- PITR (point-in-time recovery) — not available on Railway free tier
