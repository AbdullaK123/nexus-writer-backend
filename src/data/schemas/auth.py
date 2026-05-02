from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic import EmailStr
from typing import Optional
from datetime import datetime
import re
from src.infrastructure.config import config


class RegistrationData(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    profile_img: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.match(config.auth.password_pattern, v):
            raise ValueError(
                "Password must be at least 8 characters and contain "
                "an uppercase letter, lowercase letter, digit, and special character"
            )
        return v


class AuthCredentials(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    profile_img: Optional[str]


class ConnectionDetails(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# ─── Repository row models ───────────────────────────────────────────────────
# Returned by UserRepository / SessionRepository. These replace direct use of
# the Tortoise model classes in the service layer.

class UserRow(BaseModel):
    """One row from the `user` table. Includes password_hash — do NOT return
    this to the API; convert to `UserResponse` first."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    password_hash: str
    profile_img: Optional[str]
    created_at: datetime
    updated_at: datetime


class SessionRow(BaseModel):
    """One row from the `session` table."""
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    user_id: str
    expires_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    updated_at: datetime
