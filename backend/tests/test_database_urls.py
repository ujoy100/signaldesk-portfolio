"""Database URL conversion tests."""

from sqlalchemy.engine import make_url

from backend.app.db.urls import postgres_checkpoint_url


def test_checkpoint_url_preserves_and_escapes_credentials() -> None:
    source = make_url(
        "postgresql+psycopg://telecom_test:p%40ss%2Fword@db.example/telecom_test_db"
    )

    converted = postgres_checkpoint_url(source)

    assert "***" not in converted
    assert converted.startswith("postgresql://telecom_test:p%40ss%2Fword@")
    assert make_url(converted).password == "p@ss/word"
