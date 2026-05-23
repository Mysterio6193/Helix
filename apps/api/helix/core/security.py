"""Symmetric encryption of stored OAuth credentials."""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from helix.core.config import settings


def _derive_key() -> bytes:
    raw = hashlib.sha256(settings.encryption_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(raw)


_fernet = Fernet(_derive_key())


def encrypt(plaintext: str) -> bytes:
    return _fernet.encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext: bytes) -> str:
    return _fernet.decrypt(ciphertext).decode("utf-8")
