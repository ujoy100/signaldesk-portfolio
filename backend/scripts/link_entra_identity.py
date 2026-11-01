"""Explicitly link one Entra subject to an existing database-authorized user."""

import argparse

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.models.external_identity import ExternalIdentity
from backend.app.models.role import Role
from backend.app.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--entra-subject", required=True)
    args = parser.parse_args()
    settings = Settings()
    if not settings.entra_tenant_id:
        raise RuntimeError("ENTRA_TENANT_ID must be configured")
    engine = create_engine(settings.database_url)
    with Session(engine) as session:
        row = session.execute(
            select(User, Role.name)
            .join(Role)
            .where(User.id == args.user_id, User.is_active.is_(True))
        ).one_or_none()
        if row is None:
            raise RuntimeError("Active application user not found")
        if session.scalar(
            select(ExternalIdentity).where(
                ExternalIdentity.provider == "entra",
                ExternalIdentity.user_id == args.user_id,
            )
        ):
            raise RuntimeError("Application user already has an Entra identity")
        session.add(
            ExternalIdentity(
                user_id=args.user_id,
                provider="entra",
                tenant_id=settings.entra_tenant_id,
                subject=args.entra_subject,
            )
        )
        session.commit()
        print(f"Linked Entra identity to user {args.user_id} with role {row[1]}")
    engine.dispose()


if __name__ == "__main__":
    main()
