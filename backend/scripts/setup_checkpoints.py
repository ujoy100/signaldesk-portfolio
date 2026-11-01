"""Explicitly provision official LangGraph PostgreSQL checkpoint tables."""

from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy.engine import URL

from backend.app.core.config import get_settings
from backend.app.db.urls import postgres_checkpoint_url


def setup_checkpoint_schema(database_url: str | URL) -> None:
    """Idempotently provision the official LangGraph checkpoint schema."""

    url = postgres_checkpoint_url(database_url)
    with PostgresSaver.from_conn_string(url) as saver:
        saver.setup()


def main() -> None:
    setup_checkpoint_schema(get_settings().database_url)
    print("LangGraph checkpoint schema is ready.")


if __name__ == "__main__":
    main()
