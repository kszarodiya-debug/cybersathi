"""Password hashing helpers using Argon2id via pwdlib."""

from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password with the recommended Argon2id configuration."""

    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password without exposing hashing implementation details."""

    try:
        return password_hasher.verify(password, password_hash)
    except Exception:
        # Treat malformed or legacy hashes as a failed authentication attempt.
        return False
