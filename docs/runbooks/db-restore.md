# Runbook — Database restore from Railway snapshot

**Last updated:** 2026-05-13
**Applies to:** Railway-hosted Postgres (Cycle 1 deployment)

Railway takes daily automated backups of all Postgres services. Snapshots are retained for 7 days. This runbook covers restoring from a snapshot to a new database and cutting over the application.

---

## Prerequisites

- Access to the Railway project dashboard
- Ability to update environment variables on the web, worker, and beat services
- A maintenance window if the restore involves data written after the snapshot (expect up to 24 hours of data loss)

---

## Step 1 — Identify the snapshot to restore

1. Open [railway.app](https://railway.app) and navigate to your project.
2. Click the **Postgres** service.
3. Go to the **Backups** tab (or **Data** > **Backups** depending on Railway's current UI).
4. Locate the snapshot you want to restore. Snapshots are timestamped. Note the UTC time so you can estimate data loss.

---

## Step 2 — Restore to a new database

Do not restore over the existing database in place — this is irreversible and affects the live application immediately.

1. Click **Restore** on the chosen snapshot.
2. Select **Restore to new database** (not "restore in place").
3. Railway provisions a new Postgres service in the same project. This takes 2–5 minutes.
4. Once provisioned, click the new Postgres service and copy the `DATABASE_URL` connection string from its **Connect** tab.

---

## Step 3 — Verify the restored database

Before cutting over, confirm the restored data looks correct:

```bash
# Connect to the restored database directly (use the DATABASE_URL from Step 2)
psql "<new-DATABASE_URL>"

-- Check row counts on key tables
SELECT COUNT(*) FROM accounts_userprofile;
SELECT COUNT(*) FROM clients_client;
SELECT COUNT(*) FROM dashboard_dailymetricscache;
SELECT MAX(created_at) FROM core_apirequestlog;
\q
```

If row counts and timestamps match your expectations for the chosen snapshot, proceed.

---

## Step 4 — Cut over the application

Update `DATABASE_URL` in all three application services (web, worker, beat):

1. Click the **web** service → **Variables** tab.
2. Find `DATABASE_URL` and replace it with the connection string from the restored database.
3. Repeat for the **worker** and **beat** services.

---

## Step 5 — Redeploy

Trigger a fresh deployment for all three services so they pick up the new `DATABASE_URL`:

1. Click the **web** service → **Deployments** tab → **Redeploy** on the latest deployment.
2. Repeat for **worker** and **beat**.

Alternatively, push a no-op commit to `main` to trigger CI/CD:

```bash
git commit --allow-empty -m "chore: trigger redeploy after db restore"
git push origin main
```

---

## Step 6 — Verify the application is healthy

1. Open `https://<your-railway-domain>/healthz` — should return `200 OK` with `{"status": "ok"}`.
2. Log in and confirm the dashboard loads data from the restored snapshot.
3. Check that `DailyMetricsCache` row counts in the admin match expectations:

```bash
uv run python manage.py shell -c "
from apps.dashboard.models import DailyMetricsCache
print(DailyMetricsCache.objects.count(), 'rows in cache')
"
```

4. Check Sentry for any new errors from the cutover.

---

## Step 7 — Clean up the old database (after confidence period)

Once you have confirmed the restore is working correctly and no rollback is needed (typically 24–48 hours):

1. Delete the **original** Postgres service from the Railway project dashboard.
2. Update any monitoring, alerts, or external references that pointed to the old database URL.

---

## Point-in-time recovery (PITR)

Railway does not expose PITR on the free or Developer tier. The current backup strategy is daily snapshots, so the maximum data loss is up to 24 hours.

For production workloads where 24-hour data loss is unacceptable:

- Upgrade to a Railway tier that includes PITR, or
- Set up a read replica or shadow replication to an external managed Postgres (e.g., Supabase, Neon, or RDS) via logical replication.

---

## Rollback

If the restored database causes unexpected issues and you need to revert to the original:

1. The original Postgres service is still running (you restored to a *new* database, not in-place).
2. Revert `DATABASE_URL` in all three services back to the original connection string.
3. Redeploy.
