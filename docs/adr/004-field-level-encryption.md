# ADR 004 — Custom Fernet field encryption over django-cryptography

Date: 2026-05-13
Status: Accepted

## Context

Meta access tokens must be stored at rest. They are long-lived credentials that grant write access to ad accounts. Storing them in plaintext is not acceptable even in a single-tenant deployment.

The standard Django solution for transparent field-level encryption is `django-cryptography`. It wraps Django model fields with Fernet encryption transparently — the same `encrypt(models.TextField())` usage pattern we ultimately adopted.

**The problem:** `django-cryptography` 1.1 (the current release as of early 2026) imports `django.utils.baseconv`, which was removed in Django 5.0. The import fails immediately on `django.setup()`. There is no maintained fork or patch released upstream. The project is effectively broken on Django 5.x.

Options considered:

- **Wait for a fixed django-cryptography release**: No active maintenance visible. Timeline unknown.
- **Pin to Django 4.2 LTS**: Would require downgrading the entire project. Not acceptable when Django 5.2 is the current LTS.
- **Use a different library (e.g., django-encrypted-fields)**: Various forks exist but none have production traction or active maintenance.
- **Roll a minimal custom implementation**: Fernet is straightforward. The core is ~50 lines: derive a key, encrypt on write, decrypt on read, store as BinaryField. No pickle, no custom serializers.

## Decision

Implement a minimal custom field-level encryption layer in `apps/clients/fields.py`. The public API is a single function `encrypt(field_instance)` that wraps any Django field with transparent Fernet encryption, identical to the intended django-cryptography API. The implementation uses `cryptography.fernet.Fernet` directly, stores ciphertext as raw UTF-8-encoded bytes in a `BinaryField`, and supports MultiFernet for key rotation.

Key derivation: if `CRYPTOGRAPHY_KEY` is set in settings, it is used directly (must be a base64url-encoded 32-byte key). If not set (dev environments), a key is derived deterministically from `SECRET_KEY` via SHA-256. This fallback is documented and intentionally fragile — rotating `SECRET_KEY` without a `CRYPTOGRAPHY_KEY` breaks decryption of stored tokens.

## Consequences

**Positive:**
- Works on Django 5.2 without any patches.
- The codebase owns the encryption logic — no dependency on an unmaintained library.
- No pickle: values are raw UTF-8 strings. Safer than the pickle-based approach some older encryption libraries used.
- MultiFernet is supported in the rotation runbook, enabling re-encryption without a maintenance window.
- `CRYPTOGRAPHY_KEY` env var makes the key explicit and auditable.

**Negative:**
- ~150 lines of custom code to maintain. Any bugs are ours.
- Field migration handling requires care — the `deconstruct()` method must be correct or Django's migration autodetector will generate spurious migrations.
- `CRYPTOGRAPHY_KEY` must be set in production and treated as a high-value secret. If it is lost, all stored tokens are permanently unrecoverable. See `docs/runbooks/fernet-key-rotation.md` for backup and rotation procedure.
- Lookups on encrypted fields are disabled (except `isnull`). You cannot filter `ClientMetaCredentials.objects.filter(access_token="foo")` — the field stores ciphertext. This is by design.

The custom implementation is the right call given the upstream breakage. It should be replaced with a maintained library if one emerges that supports Django 5.x.
