"""
Router de autenticación - Agnóstico del proveedor
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.models.schemas import Token, UserOut, TokenRefresh, UserRegister, UserLogin
from app.core.auth import (
    get_auth_provider,
    get_current_user,
    get_current_user_with_db
)
from app.core.auth.base import IdentityProvider, UserInfo

router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_provider: IdentityProvider = Depends(get_auth_provider)
):
    """Login con formulario (compatible con Swagger OAuth2)"""
    token_response = auth_provider.login(form_data.username, form_data.password)
    return Token(**token_response.dict())

@router.post("/login/json", response_model=Token)
def login_json(
    user_data: UserLogin,
    auth_provider: IdentityProvider = Depends(get_auth_provider)
):
    """Login con JSON (más cómodo para apps)"""
    token_response = auth_provider.login(user_data.username, user_data.password)
    return Token(**token_response.dict())

@router.post("/register", status_code=201, response_model=UserOut)
def register(
    user_data: UserRegister,
    auth_provider: IdentityProvider = Depends(get_auth_provider)
):
    """Registro agnóstico del proveedor"""
    user_info = auth_provider.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    # Sincronizar con DB local
    from app.core.database.database import get_session
    from app.models.user import User
    from sqlmodel import Session
    
    with next(get_session()) as session:
        user = User(
            keycloak_id=user_info.user_id,
            username=user_info.username,
            email=user_info.email
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return UserOut(
            id=user.id,
            keycloak_id=user.keycloak_id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            profile_completed=user.profile_completed,
            created_at=user.created_at,
            roles=user_info.roles
        )

@router.get("/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user_with_db)):
    """Perfil del usuario actual"""
    user_info: UserInfo = current_user["user_info"]
    from app.models.user import User
    db_user: User = current_user["db_user"]
    
    return UserOut(
        id=db_user.id,
        keycloak_id=db_user.keycloak_id,
        username=db_user.username,
        email=db_user.email,
        is_active=db_user.is_active,
        profile_completed=db_user.profile_completed,
        created_at=db_user.created_at,
        roles=user_info.roles
    )
