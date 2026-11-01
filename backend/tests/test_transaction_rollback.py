"""Tests for PostgreSQL transaction rollback isolation."""

from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine


def test_transaction_rollback(test_db_engine: Engine) -> None:
    """Verify a row written in a test transaction does not persist."""

    customer_number = f"ROLLBACK-{uuid4().hex[:20]}"

    with test_db_engine.connect() as connection:
        transaction = connection.begin()
        connection.execute(
            text(
                """
                INSERT INTO customers (customer_number, full_name, email)
                VALUES (:customer_number, 'Rollback Probe', NULL)
                """
            ),
            {"customer_number": customer_number},
        )
        assert (
            connection.execute(
                text(
                    "SELECT COUNT(*) FROM customers "
                    "WHERE customer_number = :customer_number"
                ),
                {"customer_number": customer_number},
            ).scalar_one()
            == 1
        )
        transaction.rollback()

    with test_db_engine.connect() as connection:
        count = connection.execute(
            text(
                "SELECT COUNT(*) FROM customers "
                "WHERE customer_number = :customer_number"
            ),
            {"customer_number": customer_number},
        ).scalar_one()

    assert count == 0
