"""Safety checks for PostgreSQL integration tests."""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url


def create_test_engine() -> Engine:
    """Connect only to the dedicated telecom test database."""

    database_url = os.environ.get("TEST_DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "TEST_DATABASE_URL must be set for database integration tests."
        )

    parsed_url = make_url(database_url)

    if parsed_url.get_backend_name() != "postgresql":
        raise RuntimeError("Integration tests require PostgreSQL.")

    if parsed_url.database != "telecom_test_db":
        raise RuntimeError("Refusing to run integration tests outside telecom_test_db.")

    engine = create_engine(database_url, pool_pre_ping=True)

    try:
        with engine.connect() as connection:
            actual_database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        if actual_database != "telecom_test_db":
            raise RuntimeError(f"Unsafe database connection: {actual_database}")

    except Exception:
        engine.dispose()
        raise

    return engine
