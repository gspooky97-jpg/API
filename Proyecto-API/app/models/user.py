"""
Modelo de Usuario Local (sincronizado con Keycloak)
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    keycloak_id: str = Field(unique=True, index=True)
    username: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    
    # Campos específicos de tu aplicación
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
    profile_completed: bool = Field(default=False)

