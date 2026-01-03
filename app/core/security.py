import bcrypt
from app.config.settings import app_config
import secrets
import json
from cryptography.fernet import Fernet, InvalidToken
from typing import Union

cipher = Fernet(app_config.cookie_encryption_key)

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_session_id() -> str:
    return secrets.token_urlsafe(32)

def encrypt_session_data(data: dict) -> str:
    as_bytes = json.dumps(
        data,
        separators=(",", ":")
    ).encode('utf-8')
    encrypted = cipher.encrypt(as_bytes)
    return encrypted.decode('utf-8')

def decrypt_session_data(fernet_token: Union[bytes, str]) -> dict:
    try:
        if isinstance(fernet_token, str):
            fernet_token = fernet_token.encode('utf-8')
        decrypted_bytes = cipher.decrypt(fernet_token)
        return json.loads(decrypted_bytes.decode())
    except InvalidToken:
        return {}
    except Exception as e:
        print(f"Decryption error: {e}")  
        return {}