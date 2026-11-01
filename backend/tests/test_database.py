"""Tests for PostgreSQL database connectivity."""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def test_database_connection(test_db_engine: Engine) -> None:
    """Verify that integration tests use the isolated database."""

    with test_db_engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    assert database_name == "telecom_test_db"
