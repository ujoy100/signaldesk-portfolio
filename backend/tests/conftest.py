"""Shared fixtures for backend tests."""

from collections.abc import Iterator

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.engine import Engine

from backend.tests.db_safety import create_test_engine


@pytest.fixture
def test_db_engine() -> Iterator[Engine]:
    """Provide an isolated PostgreSQL test engine."""

    engine = create_test_engine()

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def test_db_connection(test_db_engine: Engine) -> Iterator[Connection]:
    """Provide a test connection with automatic rollback."""

    with test_db_engine.connect() as connection:
        transaction = connection.begin()

        try:
            yield connection
        finally:
            if transaction.is_active:
                transaction.rollback()


@pytest.fixture(autouse=True)
def require_current_test_schema(
    request: pytest.FixtureRequest,
) -> None:
    """Fail database tests clearly when the isolated schema is not at head."""

    if "test_db_engine" not in request.fixturenames:
        return

    test_db_engine: Engine = request.getfixturevalue("test_db_engine")
    with test_db_engine.connect() as connection:
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()

    assert revision == "2d4f8a71c930", (
        "telecom_test_db is not at the expected Alembic head; run the documented "
        "test-database upgrade command"
    )
