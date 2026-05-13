# Cycle 1 — Foundation, Auth, and Read-Only Dashboard

**Status:** Draft (awaiting user review)
**Date:** 2026-05-13
**Author:** Suyash + Claude (brainstorming session)
**Project:** One — Performance Marketing Portal

---

## 1. Context

A solo operator manages Meta Ads for **10–30 clients** with **$10k–$50k/day** total spend. The current workflow leans on Meta Ads Manager, Google Sheets, and ad-hoc tooling. Pain points span four areas: spotting underperformers fast, lead-to-sale attribution, making safe write actions on mobile, and tracking creative production. The full vision is a 14-app Django portal with Telegram approval gates, Slack commands, AI ad generation, etc.

**This spec covers only Cycle 1**, the first vertical slice. The remaining 11 sub-projects each get their own spec cycle.

### 1.1 Constraints and preferences

- Solo operator — no multi-tenant isolation, RBAC, or billing surface needed.
- Passion project, **no deadline** — quality and foundations over speed.
- Stack license: **Django + HTMX + Alpine + Tailwind + ApexCharts** (chosen over Inertia/React SPA approaches because solo + admin-UI shape favours server-rendered).
- Visual direction: **Stripe-style** — light theme, KPI cards, big charts, generous whitespace, Inter font. Power-user keyboard shortcuts layered on top.
- Stack versions: Python 3.13, Django 5.2 LTS, Postgres 16, Redis 7 (modernized from the original doc's 3.11 / 4.2).

### 1.2 Goal of Cycle 1

By the end of Cycle 1, the operator can:

1. Log in via Facebook OAuth.
2. Register and edit client records (with encrypted Meta credentials per client).
3. View a polished, read-only dashboard showing today vs. yesterday across all active accounts, with per-client drill-downs and exports.
4. Have yesterday's metrics auto-cached nightly without manual intervention.
5. Operate on a foundation (CI, tests, observability, deploy) that every later cycle inherits.

Cycle 1 explicitly does **not** include any write operations against the Meta API, the Telegram approval gate, or any of the other 11 future apps.

---

## 2. Stack

| Layer | Choice | Notes |
|---|---|---|
| Python | 3.13 | Latest stable, large perf gains over 3.11 |
| Web framework | Django 5.2 LTS | Supported through April 2028 |
| Database | PostgreSQL 16 | JSONB, partial indexes, BRIN, generated columns |
| Cache & broker | Redis 7 | Cache + Celery broker; one instance is enough |
| Task queue | Celery 5.4 + `django-celery-beat` | DB-backed schedule editable from admin |
| Web server | gunicorn + uvicorn worker | Async-ready |
| Static assets | WhiteNoise | Manifest + brotli |
| Dependency mgmt | `uv` | 10–100× faster than pip; lockfile in repo |
| Frontend build | Vite | Outputs to `static/dist/` |
| Templates | `django-cotton` | Slotted component templates |
| HTMX integration | htmx 2.x + `django-htmx` | Helper middleware, `request.htmx` |
| Charts | ApexCharts | Stripe-quality, free, HTMX-friendly |
| Encryption | `django-cryptography` (Fernet) | `EncryptedTextField` for tokens |
| Logging | structlog | JSON in prod, pretty in dev |
| Error tracking | Sentry | Django + Celery integrations |
| Lint/format | Ruff | Replaces black + isort + flake8 + pyupgrade |
| Type check | mypy + django-stubs (strict mode) | Enforced in CI |
| Tests | pytest, pytest-django, factory-boy, responses, freezegun | Postgres-backed test DB |
| Migration safety | django-migration-linter | CI gate |
| Pre-commit | pre-commit | ruff, mypy, eof-fixer, yamllint, sqlfluff |
| Auth | django-allauth (Facebook provider) | Sessions; no token plumbing |
| Deploy | Railway with nixpacks | 3 processes: web/worker/beat |

---

## 3. Project structure

```
one/
├── apps/
│   ├── accounts/              # users, profile, approval gate, allauth glue
│   ├── clients/               # Client, ClientMetaCredentials, MetaAdAccount
│   ├── dashboard/             # DailyMetricsCache, dashboard views, exports
│   ├── core/                  # ActivityLog, APIRequestLog, middleware, base templates
│   └── design_system/         # component showroom (dev-only)
├── services/
│   └── meta_api/              # HTTP client, token resolver, retry, insights helpers
│       ├── __init__.py
│       ├── client.py          # httpx Client wrapper with retries + rate-limit handling
│       ├── tokens.py          # cascading token resolution
│       ├── insights.py        # /act_<id>/insights helpers
│       ├── accounts.py        # /act_<id> helpers
│       ├── errors.py          # error taxonomy
│       └── tests/
├── one/                       # Django project package
│   ├── settings/{base,dev,prod,test}.py
│   ├── celery.py
│   ├── urls.py, wsgi.py, asgi.py
├── frontend/
│   ├── src/
│   │   ├── main.js            # HTMX, Alpine, ApexCharts init
│   │   ├── styles/tailwind.css
│   │   └── components/        # Alpine.js components
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── postcss.config.js
├── templates/
│   ├── base.html
│   ├── cotton/                # <c-button>, <c-stat-card>, etc.
│   └── partials/
├── static/                    # vite output, collectstatic dest (gitignored)
├── tests/                     # cross-cutting integration tests
├── docs/
│   ├── superpowers/specs/     # this file + future cycles
│   ├── adr/                   # architecture decision records
│   └── runbooks/              # ops procedures
├── deploy/
│   ├── Procfile
│   ├── railway.toml
│   └── nixpacks.toml
├── .github/workflows/{ci.yml, deploy.yml}
├── pyproject.toml             # uv, ruff, mypy, pytest, coverage config
├── uv.lock
├── manage.py
├── .env.example
├── .pre-commit-config.yaml
└── README.md
```

**Conventions:**
- Apps live under `apps/`. `INSTALLED_APPS` uses dotted paths (`apps.accounts`).
- `services/` holds external API integrations. **No Django models** live here.
- Settings split four ways: `base.py` (shared), `dev.py`, `prod.py`, `test.py`. `DJANGO_SETTINGS_MODULE` chosen via env var.
- Every app has its own `tests/` directory.

---

## 4. Data model

### 4.1 `accounts` app

**`UserProfile`** (1:1 with auth `User`)

| Field | Type | Notes |
|---|---|---|
| user | OneToOne(User) | PK |
| timezone | Char | IANA tz, default `Asia/Kolkata` |
| is_approved | Boolean | Default false; bypassed if email in `OwnerAllowlist` |
| default_account | FK(MetaAdAccount, null=True) | UI preference |
| created_at | DateTime | |

**`OwnerAllowlist`** (singleton via `django-solo`)

| Field | Type | Notes |
|---|---|---|
| emails | JSONField (list of str) | Auto-approved emails |
| auto_approve | Boolean | Master switch |

Seeded on first migration from `OWNER_EMAILS` env var. Editable from admin afterward without redeploy.

### 4.2 `clients` app

**`Client`**

| Field | Type | Notes |
|---|---|---|
| name | Char(120) | |
| slug | SlugField, unique | URL-safe identifier |
| is_active | Boolean | Default true |
| target_roas | Decimal(6,2), null | Per-client goal |
| target_cpl | Decimal(8,2), null | |
| target_cpa | Decimal(8,2), null | |
| min_test_spend | Decimal(8,2), null | |
| notes | TextField, blank | |
| created_at, updated_at | DateTime | |

**`ClientMetaCredentials`** (1:1 with Client, separate so token rotation has audit trail)

| Field | Type | Notes |
|---|---|---|
| client | OneToOne(Client) | PK |
| access_token | EncryptedTextField | Fernet-encrypted at rest |
| fallback_token | EncryptedTextField, blank | |
| api_version | Char(8) | Default `"v22.0"` |
| last_validated_at | DateTime, null | Set by token-validation task |

**`MetaAdAccount`**

| Field | Type | Notes |
|---|---|---|
| client | FK(Client) | |
| account_id | Char(40), unique | Meta's `act_xxx` |
| account_name | Char(120) | |
| currency | Char(3) | ISO 4217 |
| timezone_offset | Int | Minutes from UTC |
| is_active | Boolean | Default true |
| last_sync_at | DateTime, null | |
| last_error | TextField, blank | Last sync error if any |
| created_at, updated_at | DateTime | |

Indexes: `(client_id, is_active)`, partial `(slug)` on Client where `is_active = true`.

### 4.3 `dashboard` app

**`DailyMetricsCache`** — unique on `(account, date)`

| Field | Type | Notes |
|---|---|---|
| account | FK(MetaAdAccount) | |
| date | DateField | Account-local date |
| spend | Decimal(12,2) | |
| impressions | BigInt | |
| clicks | BigInt | |
| cpm | Decimal(10,4) | |
| ctr | Decimal(8,4) | |
| frequency | Decimal(8,4) | |
| reach | BigInt | |
| outbound_clicks | BigInt | |
| outbound_clicks_ctr | Decimal(8,4) | |
| landing_page_views | BigInt | |
| add_to_cart | BigInt | |
| purchases | BigInt | |
| purchase_value | Decimal(14,2) | |
| leads | BigInt | |
| fetched_at | DateTime | |
| source | Char(8) | `"manual"` or `"beat"` |

Computed properties: `cost_per_purchase`, `cost_per_lead`, `roas` (purchase_value / spend, null-safe).

Index: `(account_id, date DESC)` covers all dashboard queries.

### 4.4 `core` app (observability)

**`ActivityLog`**

| Field | Type | Notes |
|---|---|---|
| user | FK(User), null | |
| level | Char(8) | info/warn/error |
| action | Char(80) | Free-form |
| path, method | Char | |
| status_code | Int | |
| ip_address | GenericIPAddress | |
| user_agent | Char(256) | |
| duration_ms | Int | |
| request_id | UUID | Correlates with APIRequestLog |
| created_at | DateTime, indexed | |

Retention: keep 90 days, daily cleanup task (added later, not Cycle 1).

**`APIRequestLog`**

| Field | Type | Notes |
|---|---|---|
| service | Char(32) | `"meta_api"`, etc. |
| method, url | Char, Text | |
| query_params | JSONField | Token redacted |
| request_body | JSONField, null | |
| status_code | Int | |
| response_body | JSONField, null | Truncated to ~4 KB |
| duration_ms | Int | |
| error | TextField, blank | |
| user | FK(User), null | |
| client | FK(Client), null | |
| request_id | UUID | |
| created_at | DateTime, indexed | |

Token redaction is enforced in `APIRequestLog.save()`, not just at the call site — defense in depth.

### 4.5 Deltas from the original architecture doc

- **Credentials split** from `Client` into `ClientMetaCredentials` (1:1) — tokens never get accidentally loaded with the Client row.
- **`MetaAdAccount`** is its own model instead of a JSON list on Client — every later feature (campaigns, leads, funnel) joins on `MetaAdAccount`.
- **`OwnerAllowlist`** singleton instead of hardcoded env check — manageable in admin.
- **`request_id`** correlates HTTP request → outbound API calls in one query.
- **Decimal, not Float**, for all monetary fields.

---

## 5. Key flows

### 5.1 Login & approval

```
User → /auth/login/
  → AllAuth Facebook OAuth redirect
  → Facebook callback → AllAuth creates User + stores SocialToken
  → UserProfile.get_or_create(user=request.user)
  → if user.email in OwnerAllowlist.emails and OwnerAllowlist.auto_approve:
       profile.is_approved = True
  → if profile.is_approved: redirect /dashboard/
    else: redirect /pending-approval/
```

The `ApprovalRequiredMiddleware` runs on every request and short-circuits unapproved users to `/pending-approval/` (except for `/auth/*`, `/healthz`, `/static/*`, `/admin/*` for superusers).

### 5.2 Dashboard load

```
GET /dashboard/
  → DashboardOverviewView.get()
  → accounts = MetaAdAccount.objects.filter(is_active=True, client__is_active=True)
  → today_metrics = DailyMetricsCache.objects.filter(
        account__in=accounts, date__in=[today, yesterday]
      ).select_related('account__client')
  → group by client for the table, aggregate for the KPI strip
  → render with JSON island for ApexCharts hydration
```

If `today_metrics` is missing entries (e.g., not yet pulled), the row renders with a "Refresh" button. Clicking it does an **HTMX POST** to `/dashboard/accounts/<id>/refresh/` which:

1. Calls `meta_api.insights(account, date_preset='today')` (synchronous, with timeout).
2. Upserts `DailyMetricsCache`.
3. Returns an HTML fragment of the updated row.

### 5.3 Nightly metrics pull

Celery Beat schedule: every day at **00:30 IST** (after Meta's data settles for the previous day).

```python
@shared_task
def schedule_daily_pulls():
    for account in MetaAdAccount.objects.filter(is_active=True, client__is_active=True):
        pull_account_metrics.delay(account.id, date=yesterday())

@shared_task(bind=True, max_retries=5)
def pull_account_metrics(self, account_id, date):
    try:
        metrics = meta_api.insights(account, time_range={"since": date, "until": date})
        DailyMetricsCache.upsert(account, date, **metrics, source="beat")
    except RateLimitError as e:
        raise self.retry(countdown=e.retry_after, exc=e)
    except AuthError as e:
        account.last_error = str(e); account.save()
        raise   # surfaces to Sentry
```

### 5.4 Meta API call (the foundational hot path)

```
caller → meta_api.client.get(account, endpoint, **params)
  → token = resolve_token(account)         # per-client → env fallback
  → wait if rate-limit window open (Redis TTL)
  → httpx.Client.get(url, params, timeout=15, headers={"Authorization": f"Bearer {token}"})
  → on 4xx: classify into AuthError | RateLimitError | InvalidParamError | FatalError
  → on 5xx or network: retry (3x, exp backoff: 1s, 3s, 9s)
  → write APIRequestLog row (token redacted)
  → on success: return typed dataclass (e.g., InsightsRow)
```

The `services/meta_api/` module is **the** critical path. Every later feature depends on it. It carries the highest test coverage target (≥ 90%).

---

## 6. Design system v1

### 6.1 Tokens (Tailwind config)

- **Type:** Inter Variable (subset + variable), system fallback. Scale 11 / 12 / 14 / 16 / 18 / 24 / 32. Line-height 1.4 body, 1.2 headings.
- **Color:**
  - Page bg `slate-50` (`#f8fafc`)
  - Surface `white`
  - Ink `slate-900` (`#0f172a`)
  - Muted ink `slate-500`
  - Primary `indigo-600` (`#4f46e5`)
  - Success `emerald-600`
  - Danger `red-600`
  - Warn `amber-500`
- **Spacing:** 4 / 8 / 12 / 16 / 24 / 32 / 48. Card padding 16 or 24.
- **Radius:** 4 (buttons), 6 (inputs, cards), 8 (modals).
- **Shadow:** `0 1px 2px 0 rgb(0 0 0 / 0.04)` baseline; `0 4px 12px 0 rgb(0 0 0 / 0.08)` for modals.
- **Light theme only** in Cycle 1; dark theme is a Cycle ≥ 3 enhancement.

### 6.2 Cotton components

`<c-button>`, `<c-card>` (+ header/body/footer slots), `<c-stat-card>` (label/value/delta/sparkline), `<c-data-table>` (sortable headers), `<c-modal>` (HTMX-driven `<dialog>`), `<c-toast>` (auto-dismiss), `<c-form-field>` (label, error, help), `<c-date-range>` (`Litepicker`-backed Alpine widget), `<c-skeleton>` (HTMX swap loader), `<c-empty-state>`, `<c-page-header>`, `<c-sparkline>` (ApexCharts wrapper).

A **`/design-system/`** route shows a showroom of every component for visual QA. Hidden in prod by setting check.

### 6.3 Keyboard shortcuts (layered on top)

- `⌘K` / `Ctrl+K` opens command palette (stubbed in Cycle 1 — opens a placeholder; populated in later cycles).
- `g d` → Dashboard, `g c` → Clients (Vim-style "go" prefix).
- `?` opens shortcut cheat-sheet modal.

---

## 7. Observability & security

### 7.1 Observability

- **Sentry**: Django + Celery integrations, user binding, `request_id` tag, environment tag.
- **structlog**: JSON in prod, pretty in dev. Per-request context (`request_id`, `user_id`, `client_id`) bound via middleware.
- **ActivityLogMiddleware** (after Django auth): writes one row per request (skips static + healthz + log endpoints to avoid recursion).
- **APIRequestLog**: every Meta API call (via the service layer) writes one row with token redacted. Body truncated to 4 KB.
- **`/healthz`**: returns 200 if DB + Redis reachable; otherwise 503 with which dependency failed.
- **request_id**: UUID generated in `RequestIDMiddleware` (the first custom middleware); propagated into structlog, Sentry, and all log rows.
- **Prometheus**: `django-prometheus` exposes `/metrics` (admin-only in Cycle 1); future Grafana integration in a later cycle.

### 7.2 Security baseline

- HTTPS-only with HSTS (1 year, preload-ready).
- CSRF, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
- `django-csp` with `default-src 'self'`, `script-src 'self' 'nonce-...'` (no inline scripts; Alpine x-data attributes are fine, true inline `<script>` blocks get nonces), `style-src 'self' 'unsafe-inline'`.
- Session cookies: `Secure`, `HttpOnly`, `SameSite=Lax`. Session lifetime 14 days, sliding.
- `X-Robots-Tag: noindex` on every response.
- All Meta tokens encrypted at rest with Fernet (`django-cryptography`). `FERNET_KEY` env var, separate from `SECRET_KEY`.
- `django-ratelimit` on `/auth/*`: 5 attempts/min/IP for login.
- No PII in logs: `APIRequestLog.save()` actively redacts `access_token`, `appsecret_proof`, `client_secret` fields.
- Secrets only via env vars; `.env.example` checked in with placeholders, `.env` in `.gitignore`.
- `pip-audit` + Dependabot in CI.

### 7.3 Middleware stack (in order)

1. `SecurityMiddleware`
2. `WhiteNoiseMiddleware`
3. `RequestIDMiddleware` (custom — generates UUID, binds to structlog)
4. `SessionMiddleware`
5. `CommonMiddleware`
6. `CsrfViewMiddleware`
7. `AuthenticationMiddleware`
8. `MessageMiddleware`
9. `XFrameOptionsMiddleware`
10. `CSPMiddleware` (django-csp)
11. `AllAccountMiddleware` (allauth)
12. `ApprovalRequiredMiddleware` (custom)
13. `NoIndexMiddleware` (custom — adds X-Robots-Tag)
14. `ActivityLogMiddleware` (custom — last so it sees final status code)
15. `HtmxMiddleware` (django-htmx)

---

## 8. Testing strategy

### 8.1 Tooling

- `pytest` + `pytest-django` + `pytest-cov` + `pytest-xdist` (parallel)
- **Postgres-backed** test DB (matches prod; no SQLite divergence)
- `factory-boy` for fixtures
- `responses` for HTTP mocking (Meta API)
- `freezegun` for time control
- One Playwright smoke test (login → dashboard) — runs in CI on schedule, not every PR

### 8.2 Layers

- **Unit** — models (validation, properties), service-layer functions
- **Integration** — Django test client / pytest-django; views, middleware, allauth flow
- **Smoke** — `/healthz` returns 200; `/dashboard/` renders with seeded data
- **Migration tests** — `django-migration-linter` blocks unsafe migrations (e.g., add NOT NULL without default) in CI

### 8.3 Coverage targets

| Area | Target |
|---|---|
| `services/meta_api/` | ≥ 90% |
| `apps/*/services.py`, `apps/*/models.py` | ≥ 85% |
| Overall | ≥ 70% |
| Critical paths (auth, token resolver, encryption, rate-limit handler) | ≥ 95% |

### 8.4 CI pipeline (`.github/workflows/ci.yml`)

1. `uv sync --frozen`
2. `pre-commit run --all-files` (ruff format check, ruff lint, end-of-file-fixer, yamllint, sqlfluff)
3. `mypy --strict apps services one`
4. `python manage.py makemigrations --check --dry-run`
5. `django-migration-linter`
6. `pytest -n auto --cov --cov-report=xml --cov-fail-under=70`
7. `pip-audit`
8. Coverage upload to Codecov

PRs block on red CI. Main branch deploys to Railway only if CI is green.

---

## 9. Deployment & operations

### 9.1 Railway configuration

```toml
# deploy/railway.toml
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/healthz"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

```
# deploy/Procfile
web:    gunicorn one.wsgi:application --workers 3 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
worker: celery -A one worker -l info --concurrency=2
beat:   celery -A one beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Release command (run before web starts on each deploy): `python manage.py migrate --noinput && python manage.py collectstatic --noinput`.

### 9.2 Build sequence (nixpacks)

```
1. Install Python 3.13 + Node 22
2. uv sync --frozen
3. cd frontend && npm ci && npm run build
4. python manage.py collectstatic --noinput
5. python manage.py migrate --noinput
6. start web (gunicorn) | worker (celery) | beat (celery beat)
```

### 9.3 Required env vars

| Var | Purpose |
|---|---|
| `DATABASE_URL` | Railway-provided Postgres connection string |
| `REDIS_URL` | Railway-provided Redis connection string |
| `DJANGO_SECRET_KEY` | Cookie signing, CSRF |
| `FERNET_KEY` | Field-level encryption for Meta tokens |
| `DJANGO_SETTINGS_MODULE` | `one.settings.prod` |
| `SENTRY_DSN` | Error tracking |
| `FACEBOOK_OAUTH_CLIENT_ID` / `FACEBOOK_OAUTH_CLIENT_SECRET` | AllAuth OAuth |
| `META_APP_ID` / `META_APP_SECRET` | Meta Marketing API app credentials |
| `RAILWAY_PUBLIC_DOMAIN` | CSRF trusted origin |
| `OWNER_EMAILS` | Initial seed for `OwnerAllowlist` (comma-separated) |
| `ALLOWED_HOSTS` | Comma-separated hostnames |

### 9.4 Backups & DR

- Railway provides automatic daily Postgres snapshots (retained 7 days).
- `docs/runbooks/db-restore.md` documents point-in-time recovery (manual process for now).
- Encrypted token blobs are recoverable as long as `FERNET_KEY` is preserved — `FERNET_KEY` rotation procedure (re-encrypt all encrypted fields) documented in a runbook.

### 9.5 Architecture decision records

Each major irreversible decision in this spec gets a short ADR under `docs/adr/`. Cycle 1 produces at least these ADRs:

- `001-django-htmx-over-spa.md`
- `002-uv-over-pip-tools.md`
- `003-cotton-for-templates.md`
- `004-field-level-encryption.md`
- `005-railway-deploy.md`

---

## 10. What Cycle 1 explicitly excludes

These belong to future cycle specs and **must not creep** into Cycle 1:

- Telegram approval gate & bot commands (Cycle 4)
- Slack slash commands (Cycle 12)
- Campaign / ad set / ad CRUD (Cycle 5) — **all writes against Meta API**
- A/B testing (Cycle 9)
- Automated rules engine (Cycle 7)
- Lead attribution / Google Sheets sync (Cycle 8)
- Webinars & Zoom integration (Cycle 10)
- Funnel snapshots (Cycle 10)
- Creative directory kanban (Cycle 6)
- AI ad generation (Cycle 11)
- Custom audiences / lookalikes (Cycle 6)
- Multi-user role-based access (not planned — solo)

---

## 11. Acceptance criteria for Cycle 1

The cycle is "done" when **all** of the following are true:

1. `gh repo` builds green: lint, types, migrations, tests, coverage, pip-audit.
2. A fresh deploy from `main` to Railway succeeds end-to-end via `railway.toml`.
3. `/healthz` returns 200.
4. A new user can sign in via Facebook OAuth.
5. An owner-email user is auto-approved and lands on `/dashboard/`.
6. A non-owner user is redirected to `/pending-approval/` until manually approved in admin.
7. A `Client` can be created, edited, deleted via UI.
8. A Meta token can be added to a `Client`, stored encrypted at rest (verified: a raw DB row does not contain plaintext token).
9. A `MetaAdAccount` row can be created and is queryable from the dashboard.
10. The dashboard overview renders KPIs + per-client table + sparkline charts for any seeded `DailyMetricsCache` data.
11. The "Refresh" button on a missing row calls the Meta API and writes a cache row.
12. The nightly Celery Beat job runs and produces `DailyMetricsCache` rows for the prior day.
13. Every Meta API call writes one `APIRequestLog` row with the access token redacted (verified by an automated test).
14. Sentry receives a deliberate test error and the issue appears.
15. The `/design-system/` showroom renders every component.
16. README contains "start dev locally in 5 minutes" instructions that a colleague can follow.
17. The Playwright smoke test (login → dashboard) passes against the deployed environment.

---

## 12. Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Meta API rate-limit surprises | High | Rate-limit-aware client; Redis TTL on outbound calls; ample retry headroom |
| Token leakage in logs | Medium | Defense in depth: redaction in service layer **and** in `APIRequestLog.save()`; CI grep test that fails if `EAAB` (Meta token prefix) appears in any log fixture |
| Encryption key loss | Low (catastrophic) | `FERNET_KEY` stored in Railway env + offline backup; documented rotation runbook |
| OAuth misconfig at deploy time | Medium | Add a smoke step in CI deploy that hits `/auth/login/` and expects a 302 to Facebook |
| HTMX/CSP friction | Medium | All inline `<script>` blocks use nonces (CSP middleware emits per-request nonce); `hx-headers` carries CSRF token via middleware |
| Stripe-style polish without an actual designer | Medium | TailwindUI Catalyst or shadcn-html as reference; design-system showroom forces visual consistency |

---

## 13. Open questions for the user

None blocking — proceeding to implementation plan after spec approval. Future cycles will produce their own specs; we do **not** pre-decide them here.

---

## 14. Sequence after this spec is approved

1. Invoke `superpowers:writing-plans` to produce a step-by-step implementation plan derived from this spec.
2. Set up the actual repo structure (initial scaffold, CI, deploy pipeline) per the plan.
3. Implement in plan order with TDD.
4. Cycle 1 ships → write Cycle 2 spec.
