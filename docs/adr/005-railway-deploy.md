# ADR 005 — Railway as deployment target

Date: 2026-05-13
Status: Accepted

## Context

One needs to run three long-lived processes (Django web, Celery worker, Celery Beat) plus two managed services (Postgres 16, Redis 7). The operator is a solo engineer with no DevOps background to maintain. The requirements are:

- Deploy from a git push with no manual steps
- Managed Postgres and Redis (no self-managed instances)
- Three separate process definitions from a single codebase
- Automatic TLS, health checks, and environment variable management
- Reasonable pricing at low traffic

Options considered:

- **Heroku**: Well-known PaaS, supports multi-process Procfiles, managed add-ons. More expensive than alternatives at equivalent resource levels. The 2022 free tier removal and pricing restructuring made it less attractive for early-stage projects.
- **Fly.io**: Strong multi-process support via `fly.toml`. Managed Postgres (via separate Fly Postgres app) and managed Redis (Upstash). More configuration surface area — `fly.toml` requires explicit port, memory, CPU, and health check configuration per service. Slight pricing advantage on compute; similar managed data costs. Good alternative if Railway becomes unworkable.
- **Render**: Simpler than Fly.io. Managed Postgres and Redis. Free tier is slow (spin-down on inactivity). Background workers are a paid feature.
- **Railway**: Multi-process support via `Procfile` and per-service custom start commands. Managed Postgres (with daily snapshots, 7-day retention) and managed Redis. Auto-deploys on `git push`. Environment variables shared across services in a project. Nixpacks for build detection. Reasonable Developer plan pricing.

## Decision

Deploy to Railway. Each process (web, worker, beat) is a separate Railway Service within the same Railway Project. They share environment variables. Postgres and Redis are Railway-managed services in the same project. Configuration lives in `deploy/railway.toml`, `deploy/nixpacks.toml`, and `deploy/Procfile`.

## Consequences

**Positive:**
- `git push` to `main` triggers a deploy with no additional commands.
- Three-process layout maps cleanly to Railway's multi-service project model.
- Managed Postgres includes daily automated backups with 7-day retention. Restore procedure documented in `docs/runbooks/db-restore.md`.
- Railway's environment variable UI makes rotating secrets (FERNET_KEY, SECRET_KEY, Meta tokens) straightforward.
- No infrastructure configuration files outside the `deploy/` directory.

**Negative:**
- Vendor lock-in. Railway's `railway.toml` and Nixpacks build format are Railway-specific. Migration to another platform requires rewriting deploy configuration, though the application code is portable.
- Pricing scales with resource usage. At non-trivial traffic, Railway's per-GB-RAM/per-vCPU billing can exceed Fly.io or a self-managed VPS. This is acceptable at Cycle 1 scale.
- Point-in-time recovery (PITR) is not available on the free or Developer tier. For production-critical data, upgrade to a tier that includes PITR or shadow-replicate to an external Postgres instance.
- Railway has had occasional platform incidents. Having a tested restore procedure (see runbook) is important.

Fly.io remains the most credible alternative if Railway's pricing or reliability becomes a problem.
