# Deploy configuration

Files in this folder are read by Railway:
- `railway.toml` — set Railway's "Config file" setting to `deploy/railway.toml`.
- `nixpacks.toml` — referenced by `railway.toml`.
- `Procfile` — Railway autodetects. If Railway prefers root, symlink: `ln -s deploy/Procfile Procfile` from project root.

Required environment variables (see `.env.example` for defaults):
- `DATABASE_URL`, `REDIS_URL`, `DJANGO_SECRET_KEY`, `FERNET_KEY`, `META_APP_ID`, `META_APP_SECRET`, `FACEBOOK_OAUTH_CLIENT_ID/SECRET`, `RAILWAY_PUBLIC_DOMAIN`, `ALLOWED_HOSTS`, `OWNER_EMAILS`, `SENTRY_DSN` (optional).

After first deploy, set up the worker and beat processes from the Railway UI:
- Each is a separate "Service" in the same Railway project.
- Service "worker": Custom start command `celery -A one worker -l info --concurrency=2`.
- Service "beat": Custom start command `celery -A one beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`.
- All three services share the same env vars.
