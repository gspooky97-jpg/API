"""
Interface abstracta para proveedores de identidad.
Define el contrato que debe cumplir cualquier proveedor (Keycloak, Auth0, etc.)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class UserInfo(BaseModel):
    """Información de usuario normalizada (independiente del proveedor)"""
    user_id: str  # ID único del proveedor
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: list[str] = []
    is_active: bool = True
    email_verified: bool = False
    raw_data: Dict[str, Any] = {}  # Datos originales del proveedor


class TokenResponse(BaseModel):
    """Respuesta de autenticación normalizada"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None


class IdentityProvider(ABC):
    """
    Clase abstracta que define el contrato para cualquier proveedor de identidad.
    Keycloak, Auth0, Cognito, etc. deben implementar esta interfaz.
    """
    
    @abstractmethod
    def login(self, username: str, password: str) -> TokenResponse:
        """Autentica usuario y retorna tokens"""
        pass
    
    @abstractmethod
    def decode_token(self, token: str) -> UserInfo:
        """Decodifica y valida token, retorna info del usuario"""
        pass
    
    @abstractmethod
    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresca el access token"""
        pass
    
    @abstractmethod
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = ""
    ) -> UserInfo:
        """Crea un nuevo usuario en el proveedor"""
        pass
    
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> UserInfo:
        """Obtiene información de un usuario por ID"""
        pass
    
    @abstractmethod
    def update_user(self, user_id: str, **kwargs) -> UserInfo:
        """Actualiza información del usuario"""
        pass
    
    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """Elimina un usuario"""
        pass
    
    @abstractmethod
    def assign_role(self, user_id: str, role: str) -> bool:
        """Asigna un rol a un usuario"""
        pass
    
    @abstractmethod
    def remove_role(self, user_id: str, role: str) -> bool:
        """Remueve un rol de un usuario"""
        pass
