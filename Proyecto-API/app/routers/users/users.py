"""
Router de Usuarios
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from app.models.user import User
from app.models.schemas import UserOut
from app.core.auth import require_role, get_current_user_with_db
from app.core.database.database import get_session

router = APIRouter()

@router.get("/", dependencies=[Depends(require_role("admin"))], response_model=List[UserOut])
def list_users(session: Session = Depends(get_session)):
    """
    Lista todos los usuarios (solo admins).
    """
    users = session.exec(select(User)).all()
    
    # Convertir a schema con roles vacíos (no están en DB local)
    return [
        UserOut(
            id=user.id,
            keycloak_id=user.keycloak_id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            profile_completed=user.profile_completed,
            created_at=user.created_at,
            roles=[]  # Los roles están en Keycloak, no en DB
        )
        for user in users
    ]

@router.get("/me", response_model=UserOut)
def get_current_user_profile(
    current_user: dict = Depends(get_current_user_with_db)
):
    """
    Obtiene el perfil del usuario actual.
    Combina info de Keycloak (roles) con info local (preferencias, etc).
    """
    db_user = current_user["db_user"]
    
    return UserOut(
        id=db_user.id,
        keycloak_id=db_user.keycloak_id,
        username=db_user.username,
        email=db_user.email,
        is_active=db_user.is_active,
        profile_completed=db_user.profile_completed,
        created_at=db_user.created_at,
        roles=current_user.get("roles", [])
    )

@router.patch("/me/profile", response_model=UserOut)
def update_profile(
    profile_completed: bool,
    current_user: dict = Depends(get_current_user_with_db),
    session: Session = Depends(get_session)
):
    """
    Actualiza campos específicos de la aplicación.
    NO puedes cambiar email/username (están en Keycloak).
    """
    db_user = current_user["db_user"]
    
    # Actualizar campos locales
    db_user.profile_completed = profile_completed
    from datetime import datetime
    db_user.updated_at = datetime.utcnow()
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    return UserOut(
        id=db_user.id,
        keycloak_id=db_user.keycloak_id,
        username=db_user.username,
        email=db_user.email,
        is_active=db_user.is_active,
        profile_completed=db_user.profile_completed,
        created_at=db_user.created_at,
        roles=current_user.get("roles", [])
    )
