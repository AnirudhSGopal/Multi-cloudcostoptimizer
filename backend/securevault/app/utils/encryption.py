"""
Encryption utility for cloud provider credentials.

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the `cryptography` package
for symmetric encryption of API keys, secrets, and service-account JSON
before they are stored in the database.

The encryption key is loaded from the CLOUD_ENCRYPTION_KEY env var.
If missing or invalid, a RuntimeError is raised at import time — this
is intentional so the application fails loudly on startup rather than
silently storing credentials in plaintext.
"""
import os
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# ── Load key at module level — fail loud if missing ──────────────────────────

_raw_key = os.getenv("CLOUD_ENCRYPTION_KEY")

if not _raw_key:
    raise RuntimeError(
        "CLOUD_ENCRYPTION_KEY environment variable is not set. "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
        "and add it to your .env file."
    )

try:
    _fernet = Fernet(_raw_key.encode())
except Exception as exc:
    raise RuntimeError(
        f"CLOUD_ENCRYPTION_KEY is not a valid Fernet key: {exc}"
    ) from exc


# ── Public API ───────────────────────────────────────────────────────────────

def encrypt_credential(plaintext: str) -> str:
    """
    Encrypt a plaintext string (e.g. JSON-serialized credentials).

    Returns a URL-safe base64-encoded ciphertext string suitable for
    storing in a TEXT database column.
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty string")
    token = _fernet.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_credential(ciphertext: str) -> str:
    """
    Decrypt a ciphertext string produced by encrypt_credential().

    Raises cryptography.fernet.InvalidToken if the key is wrong
    or the data has been tampered with.
    """
    if not ciphertext:
        raise ValueError("Cannot decrypt empty string")
    try:
        plaintext = _fernet.decrypt(ciphertext.encode("utf-8"))
        return plaintext.decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt credential — invalid token or wrong key")
        raise
