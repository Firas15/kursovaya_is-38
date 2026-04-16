"""
Модуль аутентификации.
Хэширование паролей через PBKDF2-SHA256 + случайная соль.
"""
import hashlib
import secrets


def hash_password(password: str) -> tuple:
    """Вернуть (salt, hash) для пароля."""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()
    return salt, hashed


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """Проверить пароль по сохранённому хэшу и соли."""
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()
    return hashed == stored_hash
