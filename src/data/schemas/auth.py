from pydantic import BaseModel, Field, field_validator
from pydantic import EmailStr
from typing import Optional
import re
from src.infrastructure.config import config

class RegistrationData(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    profile_img: Optional[str] = None

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.match(config.auth.password_pattern, v):
            raise ValueError(
                'Password must be at least 8 characters and contain '
                'an uppercase letter, lowercase letter, digit, and special character'
            )
        return v

class AuthCredentials(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    profile_img: Optional[str]

class ConnectionDetails(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
