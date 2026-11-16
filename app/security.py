"""Verificación de los tokens de sesión (JWT RS256) emitidos por auth-service.

Cada servicio verifica el token por su cuenta: no confía en que el gateway
u otro servicio ya lo haya hecho (principio de confianza cero).
"""

from dataclasses import dataclass
from functools import lru_cache

import jwt

from app.config import get_settings
from app.errors import NotAuthenticated

# Se fija el algoritmo: un token con "alg: none" o firmado con HS256 se rechaza.
JWT_ALGORITHM = "RS256"
ROLE_ADMIN = "admin"


@dataclass(frozen=True)
class AuthenticatedUser:
    """Quién hace la petición, según un token ya verificado."""

    username: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN


@lru_cache
def _public_key() -> str:
    return get_settings().jwt_public_key_file.read_text(encoding="utf-8")


def authenticate(token: str) -> AuthenticatedUser:
    """Verifica firma, vencimiento, emisor y audiencia. Falla con NotAuthenticated."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            _public_key(),
            algorithms=[JWT_ALGORITHM],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
        return AuthenticatedUser(username=str(payload["username"]), role=str(payload["role"]))
    except (jwt.InvalidTokenError, KeyError) as error:
        raise NotAuthenticated("Tu sesión no es válida o ya venció.") from error
