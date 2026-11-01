"""Destructive Alembic round-trip for one explicitly disposable database."""

import os
import subprocess
import sys
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url

EXPECTED_DATABASE = "telecom_migration_test_db"


def validate_disposable_database() -> str:
    database_url = os.environ.get("MIGRATION_TEST_DATABASE_URL")
    if not database_url:
        raise RuntimeError("MIGRATION_TEST_DATABASE_URL is required")
    if os.environ.get("ALLOW_DISPOSABLE_DB_TEST") != "yes":
        raise RuntimeError("ALLOW_DISPOSABLE_DB_TEST=yes is required")
    parsed = make_url(database_url)
    if (
        parsed.get_backend_name() != "postgresql"
        or parsed.database != EXPECTED_DATABASE
    ):
        raise RuntimeError(
            f"Refusing destructive migration test outside {EXPECTED_DATABASE}"
        )
    return database_url


def main() -> None:
    database_url = validate_disposable_database()
    environment = {**os.environ, "DATABASE_URL": database_url}
    for alembic_arguments in (
        ("upgrade", "head"),
        ("downgrade", "base"),
        ("upgrade", "head"),
        ("check",),
    ):
        subprocess.run(
            (sys.executable, "-m", "alembic", *alembic_arguments),
            check=True,
            env=environment,
        )
    safe_location = urlsplit(database_url).hostname or "local socket"
    print(f"Migration cycle passed for {EXPECTED_DATABASE} via {safe_location}")


if __name__ == "__main__":
    main()
