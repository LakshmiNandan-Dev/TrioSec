import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _fernet() -> Fernet:
    # Accept any string as key material by hashing it into a valid Fernet key.
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_encryption_key.encode()).digest())
    return Fernet(key)


def encrypt_str(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_str(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError(
            "Could not decrypt stored secret — SECRET_ENCRYPTION_KEY changed since it was saved"
        ) from exc
