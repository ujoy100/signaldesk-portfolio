"""Environment-keyed JWT authentication shared by admin and gateway boundaries."""

import jwt
from pydantic import BaseModel, ValidationError

from backend.app.core.config import Settings


class AuthenticatedPrincipal(BaseModel):
    subject: str
    role: str
    actor_id: int


class AuthenticationError(PermissionError):
    pass


def authenticate_bearer_token(token: str, settings: Settings) -> AuthenticatedPrincipal:
    """Validate an HS256 token or fail closed when auth is unconfigured."""

    if settings.auth_jwt_secret is None:
        raise AuthenticationError("Authentication is not configured")
    try:
        payload = jwt.decode(
            token,
            settings.auth_jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            audience=settings.auth_jwt_audience,
            options={"require": ["sub", "role", "actor_id", "exp", "aud"]},
        )
        return AuthenticatedPrincipal(
            subject=payload["sub"],
            role=payload["role"],
            actor_id=payload["actor_id"],
        )
    except (jwt.PyJWTError, ValidationError, KeyError, TypeError) as error:
        raise AuthenticationError("Invalid authentication token") from error
