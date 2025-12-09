"""
Schemas para request/response
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserOut(BaseModel):
    id: Optional[int]
    keycloak_id: str
    username: str
    email: Optional[str]
    is_active: bool
    profile_completed: bool
    created_at: datetime
    roles: List[str] = []  # Roles de Keycloak


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    """Schema para registro de nuevos usuarios"""
    username: str
    email: EmailStr
    password: str
    first_name: str = ""
    last_name: str = ""


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None


class TokenRefresh(BaseModel):
    refresh_token: str


class KeycloakUser(BaseModel):
    username: str
    email: Optional[str]
    sub: str
    name: Optional[str]
    given_name: Optional[str]
    family_name: Optional[str]
    roles: List[str]
    email_verified: bool
