from passlib.context import CryptContext
from app.config.settings import app_config
import secrets
import json
from cryptography.fernet import Fernet, InvalidToken
from typing import Union

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
cipher = Fernet(app_config.cookie_encryption_key)

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

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
        # Handle both bytes and string input
        if isinstance(fernet_token, str):
            fernet_token = fernet_token.encode('utf-8')
        decrypted_bytes = cipher.decrypt(fernet_token)
        return json.loads(decrypted_bytes.decode())
    except InvalidToken:
        return {}
    except Exception as e:
        print(f"Decryption error: {e}")  
        return {}