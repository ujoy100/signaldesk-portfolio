"""Integration tests for deterministic fictional seed data."""

from sqlalchemy import Connection, func, select

from backend.app.db.seed import (
    CUSTOMERS,
    PLANS,
    ROLES,
    TICKETS,
    USERS,
    seed_fictional_data,
)
from backend.app.models.customer import Customer
from backend.app.models.plan import Plan
from backend.app.models.role import Role
from backend.app.models.subscription import Subscription
from backend.app.models.ticket import Ticket
from backend.app.models.ticket_event import TicketEvent
from backend.app.models.user import User


def _seed_counts(connection: Connection) -> dict[str, int]:
    return {
        "customers": connection.scalar(
            select(func.count())
            .select_from(Customer)
            .where(
                Customer.customer_number.in_(
                    row["customer_number"] for row in CUSTOMERS
                )
            )
        ),
        "plans": connection.scalar(
            select(func.count())
            .select_from(Plan)
            .where(Plan.plan_code.in_(row["plan_code"] for row in PLANS))
        ),
        "subscriptions": connection.scalar(
            select(func.count())
            .select_from(Subscription)
            .where(
                Subscription.started_at == next(row["created_at"] for row in CUSTOMERS)
            )
        ),
        "tickets": connection.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.ticket_number.in_(row["ticket_number"] for row in TICKETS))
        ),
        "ticket_events": connection.scalar(
            select(func.count())
            .select_from(TicketEvent)
            .join(Ticket, Ticket.id == TicketEvent.ticket_id)
            .where(Ticket.ticket_number.in_(row["ticket_number"] for row in TICKETS))
        ),
        "roles": connection.scalar(
            select(func.count()).select_from(Role).where(Role.name.in_(ROLES))
        ),
        "users": connection.scalar(
            select(func.count())
            .select_from(User)
            .where(User.email.in_(email for email, _, _ in USERS))
        ),
    }


def test_seed_data_is_complete_and_fictional(test_db_connection: Connection) -> None:
    expected = seed_fictional_data(test_db_connection)

    assert _seed_counts(test_db_connection) == expected
    assert all(row["email"].endswith(".test") for row in CUSTOMERS)
    assert all(email.endswith(".test") for email, _, _ in USERS)


def test_seed_data_is_repeatable(test_db_connection: Connection) -> None:
    expected = seed_fictional_data(test_db_connection)
    first_counts = _seed_counts(test_db_connection)

    seed_fictional_data(test_db_connection)

    assert first_counts == expected
    assert _seed_counts(test_db_connection) == expected
