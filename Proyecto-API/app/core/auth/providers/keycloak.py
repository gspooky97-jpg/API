"""
Implementación del proveedor Keycloak.
Adapta la API de Keycloak a nuestra interfaz genérica.
"""
import requests
from jose import jwt, JWTError
from functools import lru_cache
from typing import Dict, Any
from fastapi import HTTPException, status

from app.core.auth.base import IdentityProvider, UserInfo, TokenResponse


class KeycloakProvider(IdentityProvider):
    """Adaptador para Keycloak como proveedor de identidad"""
    
    def __init__(
        self,
        server_url: str,
        realm: str,
        client_id: str,
        client_secret: str
    ):
        self.server_url = server_url.rstrip('/')
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        
        # URLs de Keycloak
        self.token_url = f"{server_url}/realms/{realm}/protocol/openid-connect/token"
        self.jwks_url = f"{server_url}/realms/{realm}/protocol/openid-connect/certs"
        self.admin_url = f"{server_url}/admin/realms/{realm}"
    
    def login(self, username: str, password: str) -> TokenResponse:
        """Autenticación con Keycloak"""
        try:
            print(f"DEBUG: Intentando login en: {self.token_url}")
            print(f"DEBUG: Client ID: {self.client_id}")
            
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "password",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "username": username,
                    "password": password,
                },
                verify=False,
                timeout=10
            )
            
            print(f"DEBUG: Status code: {response.status_code}")
            print(f"DEBUG: Response: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            return TokenResponse(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expires_in=data.get("expires_in")
            )
        except requests.HTTPError as e:
            print(f"DEBUG: HTTPError - {e}")
            print(f"DEBUG: Response text: {e.response.text if e.response else 'No response'}")
            if e.response and e.response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas"
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error al conectar con el proveedor de identidad"
            )
        except Exception as e:
            print(f"DEBUG: Exception general - {type(e).__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error de conexión: {str(e)}"
            )
    
    @lru_cache()
    def _get_public_keys(self) -> Dict[str, Any]:
        """Obtiene las claves públicas de Keycloak"""
        response = requests.get(self.jwks_url, verify=False, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def decode_token(self, token: str) -> UserInfo:
        """Decodifica y valida token JWT de Keycloak"""
        try:
            jwks = self._get_public_keys()
            unverified_header = jwt.get_unverified_header(token)
            
            # Buscar la clave RSA correspondiente
            rsa_key = None
            for key in jwks.get("keys", []):
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break
            
            if not rsa_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )
            
            # Decodificar y validar token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.client_id,
                options={"verify_aud": False}
            )
            
            # Extraer roles
            roles = []
            if "realm_access" in payload:
                roles.extend(payload["realm_access"].get("roles", []))
            if "resource_access" in payload and self.client_id in payload["resource_access"]:
                roles.extend(payload["resource_access"][self.client_id].get("roles", []))
            
            # Mapear a nuestro modelo UserInfo normalizado
            return UserInfo(
                user_id=payload["sub"],
                username=payload.get("preferred_username", ""),
                email=payload.get("email"),
                first_name=payload.get("given_name"),
                last_name=payload.get("family_name"),
                roles=roles,
                email_verified=payload.get("email_verified", False),
                raw_data=payload
            )
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )
    
    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresca el access token"""
        try:
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return TokenResponse(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expires_in=data.get("expires_in")
            )
        except requests.HTTPError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado"
            )
    
    def _get_admin_token(self) -> str:
        """Obtiene token de administrador para operaciones de gestión"""
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        return response.json()["access_token"]
    
    def create_user(    self,    username: str,    email: str,    password: str,    first_name: str = "",    last_name: str = "") -> UserInfo:
        """Crea un usuario en Keycloak"""
        admin_token = self._get_admin_token()
        
        user_data = {
            "username": username,
            "email": email,
            "enabled": True,
            "emailVerified": True,
            "firstName": first_name,
            "lastName": last_name,
            "credentials": [{
                "type": "password",
                "value": password,
                "temporary": False
            }]
        }
        
        response = requests.post(
            f"{self.admin_url}/users",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"},
            verify=False,
            timeout=10
        )
        
        if response.status_code == 409:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El usuario o email ya existe"
            )
        
        # Capturar error detallado
        if response.status_code >= 400:
            error_detail = response.text
            print(f"ERROR DE KEYCLOAK: {error_detail}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error de Keycloak: {error_detail}"
            )
        
        response.raise_for_status()
        
        # Obtener ID del usuario creado
        user_id = None
        
        # Intentar obtener del header Location
        location = response.headers.get("Location")
        if location:
            user_id = location.split("/")[-1]
        
        # Si no está en Location, buscar por username (más confiable)
        if not user_id:
            import time
            time.sleep(0.5)  # Pequeña espera para que Keycloak procese
            
            search_response = requests.get(
                f"{self.admin_url}/users?username={username}&exact=true",
                headers={"Authorization": f"Bearer {admin_token}"},
                verify=False,
                timeout=10
            )
            
            if search_response.status_code == 200:
                users = search_response.json()
                if users and len(users) > 0:
                    user_id = users[0]["id"]
        
        # Si aún no tenemos user_id, error
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Usuario creado en Keycloak pero no se pudo obtener su ID"
            )
        
        return UserInfo(
            user_id=user_id,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            roles=[],
            email_verified=True
        )
 
    def get_user_by_id(self, user_id: str) -> UserInfo:
        """Obtiene un usuario por ID"""
        admin_token = self._get_admin_token()
        
        response = requests.get(
            f"{self.admin_url}/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        return UserInfo(
            user_id=data["id"],
            username=data["username"],
            email=data.get("email"),
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            is_active=data.get("enabled", True),
            email_verified=data.get("emailVerified", False),
            raw_data=data
        )
    
    def update_user(self, user_id: str, **kwargs) -> UserInfo:
        """Actualiza un usuario"""
        admin_token = self._get_admin_token()
        
        response = requests.put(
            f"{self.admin_url}/users/{user_id}",
            json=kwargs,
            headers={"Authorization": f"Bearer {admin_token}"},
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        
        return self.get_user_by_id(user_id)
    
    def delete_user(self, user_id: str) -> bool:
        """Elimina un usuario"""
        admin_token = self._get_admin_token()
        
        response = requests.delete(
            f"{self.admin_url}/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            verify=False,
            timeout=10
        )
        return response.status_code == 204
    
    def assign_role(self, user_id: str, role: str) -> bool:
        """Asigna un rol a un usuario"""
        # Implementación específica de Keycloak
        # Omitida por brevedad
        pass
    
    def remove_role(self, user_id: str, role: str) -> bool:
        """Remueve un rol de un usuario"""
        # Implementación específica de Keycloak
        # Omitida por brevedad
        pass
