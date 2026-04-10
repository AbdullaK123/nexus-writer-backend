import json
import secrets
from typing import Union

from cryptography.fernet import Fernet, InvalidToken

from src.infrastructure.config.settings import settings

cipher = Fernet(settings.cookie_encryption_key)


def generate_session_id() -> str:
    return secrets.token_urlsafe(32)


def encrypt_session_data(data: dict) -> str:
    as_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
    encrypted = cipher.encrypt(as_bytes)
    return encrypted.decode("utf-8")


def decrypt_session_data(fernet_token: Union[bytes, str]) -> dict:
    try:
        if isinstance(fernet_token, str):
            fernet_token = fernet_token.encode("utf-8")
        decrypted_bytes = cipher.decrypt(fernet_token)
        return json.loads(decrypted_bytes.decode())
    except InvalidToken:
        return {}
    except Exception:
        return {}
