"""Issue short-lived JWTs for allowlisted fictional development identities."""

import argparse
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.role import Role
from backend.app.models.ticket import Ticket
from backend.app.models.user import User

FICTIONAL_IDENTITIES = {
    "support_agent": "support.agent@example.test",
    "supervisor": "supervisor@example.test",
    "admin": "admin@example.test",
}


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=(*FICTIONAL_IDENTITIES, "ticket_id"))
    parser.add_argument("--expired", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    settings = get_settings()
    if settings.app_env == "production":
        raise RuntimeError(
            "Development acceptance credentials are disabled in production"
        )

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as session:
        if args.role == "ticket_id":
            ticket_id = session.scalar(
                select(Ticket.id).where(Ticket.ticket_number == "FIC-TKT-001")
            )
            if ticket_id is None:
                raise RuntimeError("Fictional acceptance ticket is not seeded")
            print(ticket_id)
            return

        identity = session.execute(
            select(User.id, Role.name)
            .join(Role, User.role_id == Role.id)
            .where(
                User.email == FICTIONAL_IDENTITIES[args.role],
                User.is_active.is_(True),
                Role.name == args.role,
            )
        ).one_or_none()
        if identity is None:
            raise RuntimeError("Fictional acceptance identity is not seeded and active")

    if settings.auth_jwt_secret is None:
        raise RuntimeError("AUTH_JWT_SECRET must be configured")
    expires = datetime.now(UTC) + timedelta(minutes=-1 if args.expired else 10)
    token = jwt.encode(
        {
            "sub": f"browser-acceptance-{identity.id}",
            "actor_id": identity.id,
            "role": identity.name,
            "aud": settings.auth_jwt_audience,
            "exp": expires,
        },
        settings.auth_jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    print(token)


if __name__ == "__main__":
    main()
