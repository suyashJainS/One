"""Field-level encryption for sensitive strings using Fernet.

We rolled our own minimal wrapper because `django-cryptography` 1.1 is
incompatible with Django 5.x (it imports `django.utils.baseconv`, removed in 5.0).

Limitations:
- TextField-only. Stores ciphertext as BinaryField.
- CRYPTOGRAPHY_KEY (Fernet key) is preferred; falls back to deriving a key
  from SECRET_KEY via SHA-256 if not set. **Rotating SECRET_KEY when no
  CRYPTOGRAPHY_KEY is configured will permanently break decryption of
  existing tokens.** Always set CRYPTOGRAPHY_KEY in production.
"""

from __future__ import annotations

import base64
import hashlib
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models
from django.utils.encoding import force_bytes


def _get_fernet() -> Fernet:
    key: str | None = getattr(settings, "CRYPTOGRAPHY_KEY", None)
    if key:
        raw = base64.urlsafe_b64decode(key + "==")[:32]
    else:
        # Derive 32 bytes from SECRET_KEY deterministically.
        raw = hashlib.sha256(force_bytes(settings.SECRET_KEY)).digest()
    fernet_key = base64.urlsafe_b64encode(raw[:32])
    return Fernet(fernet_key)


def _encrypt_value(value: str) -> bytes:
    fernet = _get_fernet()
    return fernet.encrypt(value.encode("utf-8"))


def _decrypt_value(data: bytes) -> str | None:
    fernet = _get_fernet()
    try:
        return fernet.decrypt(data).decode("utf-8")
    except InvalidToken:
        return None


_FIELD_CACHE: dict[type[models.Field[Any, Any]], type[models.Field[Any, Any]]] = {}


def _build_encrypted_field_class(
    base_class: type[models.Field[Any, Any]],
) -> type[models.Field[Any, Any]]:
    """Dynamically create a BinaryField subclass that encrypts via Fernet."""

    def get_internal_type(self: models.Field[Any, Any]) -> str:
        return "BinaryField"

    def get_lookup(self: models.Field[Any, Any], lookup_name: str) -> Any:
        if lookup_name != "isnull":
            return None
        return base_class.get_lookup(self, lookup_name)

    def get_transform(self: models.Field[Any, Any], lookup_name: str) -> Any:
        if lookup_name != "isnull":
            return None
        return base_class.get_transform(self, lookup_name)

    def get_db_prep_value(
        self: models.Field[Any, Any],
        value: object,
        connection: Any,
        prepared: bool = False,
    ) -> Any:
        value = models.Field.get_db_prep_value(self, value, connection, prepared)
        if value is not None:
            return connection.Database.Binary(_encrypt_value(str(value)))
        return value

    def get_db_prep_save(
        self: models.Field[Any, Any],
        value: object,
        connection: Any,
    ) -> Any:
        return models.Field.get_db_prep_save(self, value, connection)

    def from_db_value(
        self: models.Field[Any, Any],
        value: Any,
        expression: Any,
        connection: Any,
    ) -> object:
        if value is not None:
            return _decrypt_value(bytes(value))
        return value

    def deconstruct(self: models.Field[Any, Any]) -> Any:
        # Get the base class's deconstruct to extract name and kwargs.
        field_name, _base_path, _base_args, base_kwargs = base_class.deconstruct(self)
        # Build a fresh (unbound) inner field instance to pass as the arg.
        # This is what the migration writer will serialize.
        inner_field = base_class(**base_kwargs)
        return (
            field_name,
            f"{encrypt.__module__}.{encrypt.__name__}",
            [inner_field],
            {},
        )

    def clone(self: models.Field[Any, Any]) -> models.Field[Any, Any]:
        # Use our own deconstruct to reconstruct correctly.
        _name, _path, args, _kwargs = deconstruct(self)
        # args[0] is the inner field instance.
        return encrypt(args[0])

    def __eq__(self: models.Field[Any, Any], other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        # Compare by deconstructed kwargs (stable content-based equality).
        _, __, _args1, _kwargs1 = base_class.deconstruct(self)
        _, __, _args2, _kwargs2 = base_class.deconstruct(other)
        return _kwargs1 == _kwargs2 and type(self) is type(other)

    def __hash__(self: models.Field[Any, Any]) -> int:
        _, __, _args, _kwargs = base_class.deconstruct(self)
        return hash((type(self), tuple(sorted(_kwargs.items()))))

    encrypted_cls: type[models.Field[Any, Any]] = type(
        "Encrypted" + base_class.__name__,
        (base_class,),
        {
            "get_internal_type": get_internal_type,
            "get_lookup": get_lookup,
            "get_transform": get_transform,
            "get_db_prep_value": get_db_prep_value,
            "get_db_prep_save": get_db_prep_save,
            "from_db_value": from_db_value,
            "deconstruct": deconstruct,
            "clone": clone,
            "__eq__": __eq__,
            "__hash__": __hash__,
        },
    )
    return encrypted_cls


def encrypt(base_field: models.Field[Any, Any]) -> models.Field[Any, Any]:
    """Wrap *base_field* with transparent Fernet encryption.

    Args:
        base_field: An instantiated Django model field instance.

    Returns:
        A new field instance with transparent Fernet encryption.
    """
    if not isinstance(base_field, models.Field):
        raise TypeError("encrypt() requires a field *instance*, e.g. encrypt(models.TextField())")
    base_cls = type(base_field)
    if base_cls not in _FIELD_CACHE:
        _FIELD_CACHE[base_cls] = _build_encrypted_field_class(base_cls)
    # Extract constructor kwargs from the base field.
    _name, _path, _args, base_kwargs = base_field.deconstruct()
    return _FIELD_CACHE[base_cls](**base_kwargs)
