"""
Factory para crear el proveedor de identidad según configuración.
Permite cambiar de proveedor sin modificar el código de negocio.
"""
import os
from app.core.auth.base import IdentityProvider
from app.core.auth.providers.keycloak import KeycloakProvider


def get_identity_provider() -> IdentityProvider:
    """
    Factory que retorna el proveedor de identidad configurado.
    Cambia fácilmente entre Keycloak, Auth0, Cognito, etc.
    """
    provider_type = os.getenv("IDENTITY_PROVIDER", "keycloak").lower()
    
    if provider_type == "keycloak":
        return KeycloakProvider(
            server_url=os.getenv("KEYCLOAK_SERVER_URL"),
            realm=os.getenv("KEYCLOAK_REALM"),
            client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
            client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET")
        )
    else:
        raise ValueError(f"Unknown identity provider: {provider_type}")
