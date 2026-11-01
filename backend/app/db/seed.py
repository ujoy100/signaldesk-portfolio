"""Deterministic fictional telecom seed data loader."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Connection, Engine, create_engine, select
from sqlalchemy.dialects.postgresql import insert

from backend.app.core.config import get_settings
from backend.app.models.customer import Customer
from backend.app.models.plan import Plan
from backend.app.models.role import Role
from backend.app.models.subscription import Subscription
from backend.app.models.ticket import Ticket
from backend.app.models.ticket_event import TicketEvent
from backend.app.models.user import User

SEED_TIMESTAMP = datetime(2026, 1, 15, 9, 0, tzinfo=UTC)

CUSTOMERS = (
    {
        "customer_number": "FIC-CUST-001",
        "full_name": "Maya Noor",
        "email": "maya.noor@example.test",
        "created_at": SEED_TIMESTAMP,
    },
    {
        "customer_number": "FIC-CUST-002",
        "full_name": "Omar Vale",
        "email": "omar.vale@example.test",
        "created_at": SEED_TIMESTAMP,
    },
    {
        "customer_number": "FIC-CUST-003",
        "full_name": "Lina Rowan",
        "email": "lina.rowan@example.test",
        "created_at": SEED_TIMESTAMP,
    },
)

PLANS = (
    {
        "plan_code": "FIC-MOBILE-20",
        "name": "Fictional Mobile 20",
        "plan_type": "postpaid",
        "monthly_price": Decimal("12.500"),
        "data_allowance_gb": 20,
        "created_at": SEED_TIMESTAMP,
    },
    {
        "plan_code": "FIC-FIBER-500",
        "name": "Fictional Fiber 500",
        "plan_type": "broadband",
        "monthly_price": Decimal("24.000"),
        "data_allowance_gb": 1000,
        "created_at": SEED_TIMESTAMP,
    },
)

SUBSCRIPTIONS = (
    ("FIC-CUST-001", "FIC-MOBILE-20", "active"),
    ("FIC-CUST-002", "FIC-FIBER-500", "active"),
    ("FIC-CUST-003", "FIC-MOBILE-20", "suspended"),
)

TICKETS = (
    {
        "ticket_number": "FIC-TKT-001",
        "customer_number": "FIC-CUST-001",
        "plan_code": "FIC-MOBILE-20",
        "subject": "Mobile data intermittently unavailable",
        "description": "Fictional customer reports intermittent mobile data.",
        "status": "in_progress",
        "priority": "high",
    },
    {
        "ticket_number": "FIC-TKT-002",
        "customer_number": "FIC-CUST-002",
        "plan_code": "FIC-FIBER-500",
        "subject": "Fiber router activation help",
        "description": "Fictional customer needs router activation guidance.",
        "status": "resolved",
        "priority": "medium",
    },
)

TICKET_EVENTS = (
    (
        "FIC-TKT-001",
        "ticket_created",
        "Fictional mobile-data incident recorded.",
        "customer",
    ),
    (
        "FIC-TKT-001",
        "triage_started",
        "Fictional support triage started.",
        "support_agent",
    ),
    (
        "FIC-TKT-002",
        "ticket_resolved",
        "Fictional router activation guidance supplied.",
        "support_agent",
    ),
)

ROLES = ("support_agent", "supervisor", "admin")
USERS = (
    ("support.agent@example.test", "Fictional Support Agent", "support_agent"),
    ("supervisor@example.test", "Fictional Supervisor", "supervisor"),
    ("admin@example.test", "Fictional Administrator", "admin"),
)


def _upsert_catalog_rows(connection: Connection) -> None:
    customer_insert = insert(Customer).values(CUSTOMERS)
    connection.execute(
        customer_insert.on_conflict_do_update(
            index_elements=[Customer.customer_number],
            set_={
                "full_name": customer_insert.excluded.full_name,
                "email": customer_insert.excluded.email,
                "created_at": customer_insert.excluded.created_at,
            },
        )
    )

    plan_insert = insert(Plan).values(PLANS)
    connection.execute(
        plan_insert.on_conflict_do_update(
            index_elements=[Plan.plan_code],
            set_={
                "name": plan_insert.excluded.name,
                "plan_type": plan_insert.excluded.plan_type,
                "monthly_price": plan_insert.excluded.monthly_price,
                "data_allowance_gb": plan_insert.excluded.data_allowance_gb,
                "created_at": plan_insert.excluded.created_at,
            },
        )
    )


def seed_fictional_data(connection: Connection) -> dict[str, int]:
    """Upsert the fixed fictional dataset without deleting existing records."""

    _upsert_catalog_rows(connection)
    for name in ROLES:
        connection.execute(
            insert(Role)
            .values(name=name, description=f"Fictional development {name} role")
            .on_conflict_do_nothing(index_elements=[Role.name])
        )
    role_ids = dict(
        connection.execute(select(Role.name, Role.id).where(Role.name.in_(ROLES))).all()
    )
    for email, full_name, role_name in USERS:
        user_insert = insert(User).values(
            email=email,
            full_name=full_name,
            role_id=role_ids[role_name],
            is_active=True,
            created_at=SEED_TIMESTAMP,
        )
        connection.execute(
            user_insert.on_conflict_do_update(
                index_elements=[User.email],
                set_={
                    "full_name": user_insert.excluded.full_name,
                    "role_id": user_insert.excluded.role_id,
                    "is_active": True,
                },
            )
        )
    customer_ids = dict(
        connection.execute(
            select(Customer.customer_number, Customer.id).where(
                Customer.customer_number.in_(
                    row["customer_number"] for row in CUSTOMERS
                )
            )
        ).all()
    )
    plan_ids = dict(
        connection.execute(
            select(Plan.plan_code, Plan.id).where(
                Plan.plan_code.in_(row["plan_code"] for row in PLANS)
            )
        ).all()
    )

    subscription_ids: dict[tuple[str, str], int] = {}
    for customer_number, plan_code, status in SUBSCRIPTIONS:
        existing_id = connection.execute(
            select(Subscription.id).where(
                Subscription.customer_id == customer_ids[customer_number],
                Subscription.plan_id == plan_ids[plan_code],
                Subscription.started_at == SEED_TIMESTAMP,
            )
        ).scalar_one_or_none()
        values = {
            "customer_id": customer_ids[customer_number],
            "plan_id": plan_ids[plan_code],
            "status": status,
            "started_at": SEED_TIMESTAMP,
            "ended_at": None,
        }
        if existing_id is None:
            existing_id = connection.execute(
                insert(Subscription).values(**values).returning(Subscription.id)
            ).scalar_one()
        else:
            connection.execute(
                Subscription.__table__.update()
                .where(Subscription.id == existing_id)
                .values(**values)
            )
        subscription_ids[(customer_number, plan_code)] = existing_id

    for row in TICKETS:
        values = {
            "ticket_number": row["ticket_number"],
            "customer_id": customer_ids[row["customer_number"]],
            "subscription_id": subscription_ids[
                (row["customer_number"], row["plan_code"])
            ],
            "subject": row["subject"],
            "description": row["description"],
            "status": row["status"],
            "priority": row["priority"],
            "created_at": SEED_TIMESTAMP,
            "updated_at": SEED_TIMESTAMP,
        }
        ticket_insert = insert(Ticket).values(**values)
        connection.execute(
            ticket_insert.on_conflict_do_update(
                index_elements=[Ticket.ticket_number],
                set_={
                    key: value
                    for key, value in values.items()
                    if key != "ticket_number"
                },
            )
        )

    ticket_ids = dict(
        connection.execute(
            select(Ticket.ticket_number, Ticket.id).where(
                Ticket.ticket_number.in_(row["ticket_number"] for row in TICKETS)
            )
        ).all()
    )
    for ticket_number, event_type, description, actor_type in TICKET_EVENTS:
        values = {
            "ticket_id": ticket_ids[ticket_number],
            "event_type": event_type,
            "description": description,
            "actor_type": actor_type,
            "created_at": SEED_TIMESTAMP,
        }
        exists = connection.execute(
            select(TicketEvent.id).where(
                TicketEvent.ticket_id == values["ticket_id"],
                TicketEvent.event_type == event_type,
                TicketEvent.description == description,
                TicketEvent.created_at == SEED_TIMESTAMP,
            )
        ).scalar_one_or_none()
        if exists is None:
            connection.execute(insert(TicketEvent).values(**values))

    return {
        "customers": len(CUSTOMERS),
        "plans": len(PLANS),
        "subscriptions": len(SUBSCRIPTIONS),
        "tickets": len(TICKETS),
        "ticket_events": len(TICKET_EVENTS),
        "roles": len(ROLES),
        "users": len(USERS),
    }


def run_seed(engine: Engine) -> dict[str, int]:
    """Load all seed rows atomically using a caller-provided engine."""

    with engine.begin() as connection:
        return seed_fictional_data(connection)


def main() -> None:
    """Load fictional data into the configured database."""

    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        counts = run_seed(engine)
    finally:
        engine.dispose()
    summary = ", ".join(f"{name}={count}" for name, count in counts.items())
    print(f"Fictional seed data loaded: {summary}")


if __name__ == "__main__":
    main()
