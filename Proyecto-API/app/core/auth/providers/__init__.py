"""
Proveedores de identidad disponibles
"""
from app.core.auth.providers.keycloak import KeycloakProvider

__all__ = ["KeycloakProvider"]
