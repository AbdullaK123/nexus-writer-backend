from sqlmodel import SQLModel
from pydantic import EmailStr
from typing import Optional

class RegistrationData(SQLModel):
    username: str
    email: EmailStr
    password: str
    profile_img: Optional[str] = None

class AuthCredentials(SQLModel):
    email: EmailStr
    password: str

class UserResponse(SQLModel):
    username: str
    email: str
    profile_img: Optional[str]

class ConnectionDetails(SQLModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
