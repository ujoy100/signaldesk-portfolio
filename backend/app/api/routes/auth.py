"""FastAPI-controlled Entra login, callback, and server session lifecycle."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.api.routes.support import get_support_db
from backend.app.core.oidc import (
    OIDCError,
    authenticate_session,
    begin_login,
    redeem_code,
    revoke_session,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login")
def login(
    request: Request, session: Annotated[Session, Depends(get_support_db)]
) -> RedirectResponse:
    try:
        return RedirectResponse(
            begin_login(session, request.app.state.settings), status_code=302
        )
    except OIDCError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/callback")
def callback(
    request: Request,
    session: Annotated[Session, Depends(get_support_db)],
    state: str,
    code: str,
) -> RedirectResponse:
    settings = request.app.state.settings
    try:
        existing = request.cookies.get(settings.session_cookie_name)
        if existing:
            revoke_session(session, existing)
        token, csrf = redeem_code(session, settings, state=state, code=code)
    except OIDCError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)
        ) from error
    response = RedirectResponse(settings.frontend_url, status_code=303)
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        "signaldesk_csrf",
        csrf,
        max_age=settings.session_ttl_minutes * 60,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_support_db)],
) -> None:
    settings = request.app.state.settings
    raw = request.cookies.get(settings.session_cookie_name)
    if raw:
        try:
            authenticate_session(
                session,
                raw,
                request.headers.get("X-CSRF-Token"),
                require_csrf=True,
            )
        except OIDCError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error
        revoke_session(session, raw)
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        "signaldesk_csrf", path="/", secure=settings.cookie_secure, samesite="lax"
    )
