from pydantic import BaseModel
from pydantic import EmailStr
from typing import Optional

class RegistrationData(BaseModel):
    username: str
    email: EmailStr
    password: str
    profile_img: Optional[str] = None

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
