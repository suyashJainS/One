# Runbook — FERNET_KEY rotation

**Last updated:** 2026-05-13
**Applies to:** Cycle 1 deployment — `ClientMetaCredentials.access_token` / `fallback_token`

The `FERNET_KEY` (also referred to as `CRYPTOGRAPHY_KEY` in settings) encrypts all Meta access tokens stored in the database. Losing this key means permanently losing the ability to decrypt existing tokens — they cannot be recovered from the ciphertext without it.

This runbook covers:
1. Where to store the key (backup)
2. How to rotate to a new key without downtime

---

## Key backup procedure

Maintain the `FERNET_KEY` in at least three locations:

| Location | Notes |
|---|---|
| **Railway environment variables** | Canonical production copy. Updated during rotation. |
| **1Password / vault** | Offline backup. Create a secure note titled "One FERNET_KEY [date]". Include the key value and the date it was set. |
| **Optional: encrypted file in repo** | Encrypt with a strong passphrase and commit `.env.encrypted`. Useful for disaster recovery when Railway is inaccessible. Do not commit unencrypted keys. |

Rotate backups when you rotate the key (Step 7 below). Keep the old key in your vault for the 7-day retention window before destroying it.

---

## When to rotate

- Suspected key compromise (exposed in logs, accidentally committed, etc.)
- Quarterly rotation policy (if your security requirements mandate it)
- Off-boarding a team member who had access to the key
- Railway project transfer to a new account

---

## Rotation procedure

### Step 1 — Generate a new key

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output. It looks like: `abc123...` (44 base64url characters). Store it in your vault immediately before proceeding.

### Step 2 — Add the new key to Railway alongside the old key

Do not replace the old key yet. The re-encryption step below reads with the old key and writes with the new one. If you remove the old key before re-encrypting, you'll lose all tokens.

In Railway:
1. Open the **web** service → **Variables**.
2. Add a new variable `FERNET_KEY_NEW` with the new key value. (We'll rename it later.)
3. Do **not** change `FERNET_KEY` yet.

### Step 3 — Re-encrypt all tokens in a Django shell

You can run this during normal operation (no downtime required). The re-encryption loop reads each record using the current key and saves it with a MultiFernet that tries the new key first, falling back to the old.

First, update `one/settings/base.py` locally or via a temporary deploy to support `FERNET_KEY_NEW`:

```bash
# On the Railway shell or locally against the production DB (via a temporary DATABASE_URL override):
uv run python manage.py shell
```

Then in the shell:

```python
from django.conf import settings
from cryptography.fernet import Fernet, MultiFernet
from apps.clients.models import ClientMetaCredentials

old_key = settings.CRYPTOGRAPHY_KEY  # the current FERNET_KEY value
new_key = "<paste-new-key-here>"     # the key from Step 1

old_fernet = Fernet(old_key.encode())
new_fernet = Fernet(new_key.encode())

# MultiFernet tries keys in order: new first, then old
# This allows writing with the new key while still reading records
# encrypted with the old key.
mf = MultiFernet([new_fernet, old_fernet])

qs = ClientMetaCredentials.objects.all()
print(f"Re-encrypting {qs.count()} records...")

for cred in qs:
    # Read access_token — decrypted by the existing key via the field's from_db_value
    plaintext_access = cred.access_token
    plaintext_fallback = cred.fallback_token

    # Save — the field will encrypt with the current key (old)
    # We need to bypass the field and write raw Fernet ciphertext with the new key
    from django.db import connection
    new_access = mf.encrypt(plaintext_access.encode()).decode() if plaintext_access else None
    new_fallback = mf.encrypt(plaintext_fallback.encode()).decode() if plaintext_fallback else None

    ClientMetaCredentials.objects.filter(pk=cred.pk).update(
        access_token=connection.Database.Binary(
            new_fernet.encrypt(plaintext_access.encode("utf-8"))
        ) if plaintext_access else None,
        fallback_token=connection.Database.Binary(
            new_fernet.encrypt(plaintext_fallback.encode("utf-8"))
        ) if plaintext_fallback else None,
    )

print("Done. Verify reads before updating FERNET_KEY in Railway.")
```

### Step 4 — Verify reads still work with the new key

Before changing `FERNET_KEY` in Railway, verify that the re-encrypted values are readable with the new key:

```python
from cryptography.fernet import Fernet
from apps.clients.models import ClientMetaCredentials

new_key = "<paste-new-key-here>"
new_fernet = Fernet(new_key.encode())

# Pick a record and try decrypting manually
cred = ClientMetaCredentials.objects.first()
if cred:
    from django.db import connection
    row = connection.execute(
        "SELECT access_token FROM clients_clientmetacredentials WHERE id = %s",
        [cred.pk]
    ).fetchone()
    if row and row[0]:
        plaintext = new_fernet.decrypt(bytes(row[0])).decode("utf-8")
        print("Decrypted successfully:", plaintext[:10] + "...")
    else:
        print("No access_token on this record")
```

### Step 5 — Swap FERNET_KEY in Railway

1. In Railway, set `FERNET_KEY` to the new key value on all three services (web, worker, beat).
2. Remove `FERNET_KEY_NEW` (the temporary variable from Step 2).
3. Redeploy all three services.

### Step 6 — Confirm the application reads tokens correctly

```bash
# Hit the dashboard and confirm client data loads without errors
curl -s https://<your-railway-domain>/healthz

# Check Sentry for any new InvalidToken errors after the deploy
```

Also check the application logs for any `InvalidToken` exceptions, which would indicate records that were not re-encrypted in Step 3.

### Step 7 — Archive the old key, then destroy

1. Update the "One FERNET_KEY" entry in 1Password: rename the old entry to "One FERNET_KEY [old key, set YYYY-MM-DD, retired YYYY-MM-DD]" and add a destruction date 7 days from today.
2. After 7 days with no rollback events, delete the archived old key from your vault.

---

## Emergency rollback

If the rotation breaks production (tokens unreadable after deploying the new key):

1. Set `FERNET_KEY` back to the old key in all Railway services.
2. Redeploy.
3. Tokens encrypted with the old key will be readable again.
4. Tokens re-encrypted in Step 3 may not be readable with the old key alone.

To handle both: temporarily configure MultiFernet with `[old_fernet, new_fernet]` in `apps/clients/fields.py`, deploy, then run Step 3 in reverse (re-encrypt everything with the old key), then redeploy with just the old key.

---

## Notes

- `FERNET_KEY` and `CRYPTOGRAPHY_KEY` refer to the same value. The env var is `FERNET_KEY`; the Django setting is `CRYPTOGRAPHY_KEY` (see `one/settings/base.py`).
- In dev (no `FERNET_KEY` set), a key is derived from `SECRET_KEY`. Do not rely on this in production.
- The Fernet spec uses AES-128-CBC with HMAC-SHA256. The key is 32 bytes, base64url-encoded to 44 characters.
