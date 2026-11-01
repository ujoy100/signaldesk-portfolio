"""PostgreSQL integration tests for application-table constraints."""

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.exc import IntegrityError


def _assert_integrity_error(connection: Connection, statement: str) -> None:
    """Run invalid SQL in a savepoint so the outer test transaction survives."""

    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(text(statement))


def test_customer_number_is_unique(test_db_connection: Connection) -> None:
    test_db_connection.execute(
        text(
            """
            INSERT INTO customers (customer_number, full_name)
            VALUES ('TEST-UNIQUE-001', 'First Fictional Customer')
            """
        )
    )

    _assert_integrity_error(
        test_db_connection,
        """
        INSERT INTO customers (customer_number, full_name)
        VALUES ('TEST-UNIQUE-001', 'Second Fictional Customer')
        """,
    )


def test_subscription_customer_foreign_key(test_db_connection: Connection) -> None:
    _assert_integrity_error(
        test_db_connection,
        """
        INSERT INTO subscriptions (customer_id, plan_id, status)
        VALUES (-999999, -999999, 'active')
        """,
    )


def test_subscription_status_check_constraint(
    test_db_connection: Connection,
) -> None:
    _assert_integrity_error(
        test_db_connection,
        """
        INSERT INTO subscriptions (customer_id, plan_id, status)
        VALUES (-999999, -999999, 'invalid-status')
        """,
    )


def test_ticket_priority_check_constraint(test_db_connection: Connection) -> None:
    _assert_integrity_error(
        test_db_connection,
        """
        INSERT INTO tickets (
            ticket_number, customer_id, subject, description, priority
        )
        VALUES (
            'TEST-CHECK-001', -999999, 'Probe', 'Constraint probe', 'urgent'
        )
        """,
    )
