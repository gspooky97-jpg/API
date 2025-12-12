"""
Módulo de autenticación.
Expone funciones de alto nivel que usan el proveedor configurado.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.auth.base import IdentityProvider, UserInfo
from app.core.auth.factory import get_identity_provider
from app.core.database.database import get_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_auth_provider() -> IdentityProvider:
    """Dependency para obtener el proveedor de identidad"""
    return get_identity_provider()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_provider: IdentityProvider = Depends(get_auth_provider)
) -> UserInfo:
    """Obtiene el usuario actual desde el token"""
    return auth_provider.decode_token(token)

def get_current_user_with_db(
    user_info: UserInfo = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> dict:
    """
    Obtiene el usuario actual y lo sincroniza con la DB local.
    Retorna info combinada: proveedor + base de datos local.
    """
    # Buscar o crear usuario local
    user = session.exec(
        select(User).where(User.keycloak_id == user_info.user_id)
    ).first()
    
    if not user:
        from datetime import datetime
        user = User(
            keycloak_id=user_info.user_id,
            username=user_info.username,
            email=user_info.email,
            is_active=user_info.is_active,
            created_at=datetime.utcnow()
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    
    return {
        "user_info": user_info,  # Info del proveedor
        "db_user": user,         # Info de PostgreSQL
        "user_id": user.id,
        "roles": user_info.roles
    }

def require_role(required_role: str):
    """Dependency para requerir un rol específico"""
    def role_checker(user_info: UserInfo = Depends(get_current_user)):
        if required_role not in user_info.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere el rol '{required_role}'"
            )
        return user_info
    return role_checker

__all__ = [
    "get_auth_provider",
    "get_current_user",
    "get_current_user_with_db",
    "require_role",
    "oauth2_scheme"
]