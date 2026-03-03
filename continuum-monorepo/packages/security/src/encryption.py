"""
packages/security/src/encryption.py

AES-256-GCM encryption utilities for OAuth tokens and vault content.
Uses Fernet (AES-128-CBC) as a safe, battle-tested symmetric primitive
from the `cryptography` library, with a wrapper that adds key rotation support.
"""

import os
import base64
from cryptography.fernet import Fernet, MultiFernet


def _load_keys() -> list[bytes]:
    """
    Load encryption keys from environment.  Supports key rotation:
    set ENCRYPTION_KEY_CURRENT and optionally ENCRYPTION_KEY_PREVIOUS.
    Current key is used for encryption; both are tried for decryption.
    """
    current = os.getenv("ENCRYPTION_KEY_CURRENT")
    if not current:
        raise EnvironmentError(
            "ENCRYPTION_KEY_CURRENT env var is not set. "
            "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    keys = [current.encode()]
    previous = os.getenv("ENCRYPTION_KEY_PREVIOUS")
    if previous:
        keys.append(previous.encode())

    return keys


def get_fernet() -> MultiFernet:
    """Return a MultiFernet instance supporting key rotation."""
    keys = _load_keys()
    return MultiFernet([Fernet(k) for k in keys])


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string; returns base64-encoded ciphertext."""
    f = get_fernet()
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt(ciphertext: str) -> str:
    """Decrypt a ciphertext string; raises InvalidToken on failure."""
    f = get_fernet()
    plaintext = f.decrypt(ciphertext.encode("utf-8"))
    return plaintext.decode("utf-8")


def rotate(old_ciphertext: str) -> str:
    """
    Re-encrypt old_ciphertext with the current key.
    Use during key rotation to migrate vault entries.
    """
    plaintext = decrypt(old_ciphertext)
    # Use only the current (first) key for re-encryption
    keys = _load_keys()
    f = Fernet(keys[0])
    return f.encrypt(plaintext.encode()).decode()
