"""Microsoft Entra OIDC and revocable server-session primitives."""

import base64
import hashlib
import logging
import re
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
import jwt
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.models.auth_session import AuthSession
from backend.app.models.external_identity import ExternalIdentity
from backend.app.models.oidc_login import OIDCLogin
from backend.app.models.role import Role
from backend.app.models.user import User

logger = logging.getLogger(__name__)
_AADSTS_CODE = re.compile(r"AADSTS\d+")


class OIDCError(PermissionError):
    pass


def _log_failure(
    stage: str,
    error: Exception,
    *,
    status_code: int | None = None,
    provider_error: str | None = None,
    provider_code: str | None = None,
) -> None:
    """Log only allowlisted diagnostic metadata, never protocol secrets."""

    logger.warning(
        "Microsoft OIDC validation failed",
        extra={
            "oidc_stage": stage,
            "error_category": type(error).__name__,
            "provider_status": status_code,
            "provider_error": provider_error,
            "provider_code": provider_code,
        },
    )


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def oidc_enabled(settings: Settings) -> bool:
    return all(
        (
            settings.entra_tenant_id,
            settings.entra_client_id,
            settings.entra_client_secret,
        )
    )


def begin_login(session: Session, settings: Settings) -> str:
    if not oidc_enabled(settings):
        raise OIDCError("Microsoft sign-in is not configured")
    state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )
    now = datetime.now(UTC)
    session.execute(delete(OIDCLogin).where(OIDCLogin.expires_at <= now))
    session.add(
        OIDCLogin(
            state_hash=_hash(state),
            nonce=nonce,
            code_verifier=verifier,
            expires_at=now + timedelta(minutes=10),
        )
    )
    session.commit()
    query = urlencode(
        {
            "client_id": settings.entra_client_id,
            "response_type": "code",
            "redirect_uri": settings.entra_redirect_uri,
            "response_mode": "query",
            "scope": "openid profile email",
            "state": state,
            "nonce": nonce,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"https://login.microsoftonline.com/{settings.entra_tenant_id}/oauth2/v2.0/authorize?{query}"


def redeem_code(
    session: Session, settings: Settings, *, state: str, code: str
) -> tuple[str, str]:
    transaction = session.get(OIDCLogin, _hash(state))
    now = datetime.now(UTC)
    if transaction is None or transaction.expires_at <= now:
        raise OIDCError("Invalid or expired login state")
    nonce, code_verifier = transaction.nonce, transaction.code_verifier
    session.delete(transaction)
    session.commit()  # state remains single-use when the provider call fails
    token_url = f"https://login.microsoftonline.com/{settings.entra_tenant_id}/oauth2/v2.0/token"
    try:
        response = httpx.post(
            token_url,
            data={
                "client_id": settings.entra_client_id,
                "client_secret": settings.entra_client_secret.get_secret_value(),
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.entra_redirect_uri,
                "code_verifier": code_verifier,
            },
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        body = (
            error.response.json()
            if error.response.headers.get("content-type", "").startswith(
                "application/json"
            )
            else {}
        )
        description = str(body.get("error_description", ""))
        code_match = _AADSTS_CODE.search(description)
        _log_failure(
            "authorization_code_exchange",
            error,
            status_code=error.response.status_code,
            provider_error=str(body.get("error"))[:80] or None,
            provider_code=code_match.group(0) if code_match else None,
        )
        raise OIDCError("Microsoft identity validation failed") from error
    except httpx.HTTPError as error:
        _log_failure("authorization_code_exchange", error)
        raise OIDCError("Microsoft identity validation failed") from error
    try:
        id_token = response.json()["id_token"]
    except (KeyError, ValueError, TypeError) as error:
        _log_failure("token_response", error, status_code=response.status_code)
        raise OIDCError("Microsoft identity validation failed") from error
    try:
        jwks = jwt.PyJWKClient(
            f"https://login.microsoftonline.com/{settings.entra_tenant_id}/discovery/v2.0/keys",
            cache_keys=True,
            timeout=10,
        )
        key = jwks.get_signing_key_from_jwt(id_token).key
    except jwt.PyJWTError as error:
        _log_failure("jwks_or_signing_key", error)
        raise OIDCError("Microsoft identity validation failed") from error
    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=settings.entra_client_id,
            issuer=f"https://login.microsoftonline.com/{settings.entra_tenant_id}/v2.0",
            options={"require": ["sub", "oid", "tid", "nonce", "exp", "iss", "aud"]},
        )
    except jwt.PyJWTError as error:
        _log_failure("id_token_validation", error)
        raise OIDCError("Microsoft identity validation failed") from error
    if claims["nonce"] != nonce or claims["tid"] != settings.entra_tenant_id:
        _log_failure("claim_binding", OIDCError("claim mismatch"))
        raise OIDCError("Microsoft identity validation failed")
    identity = session.scalar(
        select(ExternalIdentity).where(
            ExternalIdentity.provider == "entra",
            ExternalIdentity.tenant_id == claims["tid"],
            ExternalIdentity.subject == claims["oid"],
        )
    )
    if identity is None:
        raise OIDCError("Microsoft identity is not authorized for SignalDesk")
    user = session.get(User, identity.user_id)
    if user is None or not user.is_active:
        raise OIDCError("Microsoft identity is not authorized for SignalDesk")
    raw_token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    claimed_name = claims.get("name")
    display_name = (
        claimed_name.strip()[:150]
        if isinstance(claimed_name, str) and claimed_name.strip()
        else "Microsoft user"
    )
    session.add(
        AuthSession(
            user_id=user.id,
            token_hash=_hash(raw_token),
            csrf_hash=_hash(csrf),
            display_name=display_name,
            expires_at=now + timedelta(minutes=settings.session_ttl_minutes),
        )
    )
    session.commit()
    return raw_token, csrf


def authenticate_session(
    session: Session, raw_token: str, csrf: str | None, *, require_csrf: bool
) -> tuple[int, str]:
    now = datetime.now(UTC)
    record = session.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == _hash(raw_token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
    )
    if record is None or (
        require_csrf
        and (csrf is None or not secrets.compare_digest(record.csrf_hash, _hash(csrf)))
    ):
        raise OIDCError("Invalid or expired session")
    result = session.execute(
        select(User.id, Role.name)
        .join(Role, User.role_id == Role.id)
        .where(User.id == record.user_id, User.is_active.is_(True))
    ).one_or_none()
    if result is None:
        raise OIDCError("Invalid or expired session")
    return int(result[0]), str(result[1])


def authenticated_session_display_name(session: Session, raw_token: str) -> str:
    """Return only the verified, active session's stored Entra display name."""

    record = session.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == _hash(raw_token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(UTC),
        )
    )
    return record.display_name if record is not None else "Microsoft user"


def revoke_session(session: Session, raw_token: str) -> None:
    record = session.scalar(
        select(AuthSession).where(AuthSession.token_hash == _hash(raw_token))
    )
    if record is not None:
        record.revoked_at = datetime.now(UTC)
        session.commit()
