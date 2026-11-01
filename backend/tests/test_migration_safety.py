"""Safety-guard tests for destructive migration-cycle validation."""

import pytest

from backend.scripts.verify_migration_cycle import validate_disposable_database


def test_migration_cycle_requires_explicit_opt_in(monkeypatch) -> None:
    monkeypatch.setenv(
        "MIGRATION_TEST_DATABASE_URL",
        "postgresql+psycopg:///telecom_migration_test_db",
    )
    monkeypatch.delenv("ALLOW_DISPOSABLE_DB_TEST", raising=False)

    with pytest.raises(RuntimeError, match="ALLOW_DISPOSABLE_DB_TEST"):
        validate_disposable_database()


def test_migration_cycle_rejects_non_disposable_database(monkeypatch) -> None:
    monkeypatch.setenv(
        "MIGRATION_TEST_DATABASE_URL",
        "postgresql+psycopg:///telecom_db",
    )
    monkeypatch.setenv("ALLOW_DISPOSABLE_DB_TEST", "yes")

    with pytest.raises(RuntimeError, match="Refusing destructive migration test"):
        validate_disposable_database()


def test_migration_cycle_accepts_exact_disposable_database(monkeypatch) -> None:
    database_url = "postgresql+psycopg:///telecom_migration_test_db"
    monkeypatch.setenv("MIGRATION_TEST_DATABASE_URL", database_url)
    monkeypatch.setenv("ALLOW_DISPOSABLE_DB_TEST", "yes")

    assert validate_disposable_database() == database_url
