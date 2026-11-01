# Phase 1 Command Reference

**Phase:** PostgreSQL, Alembic, and fictional telecom operational data  
**Status:** DONE  
**Last verified:** 2026-10-25

Run commands from the repository root. Never put credentials in commands, source
files, or documentation.

## Database boundaries

- `DATABASE_URL` is the application and migration connection setting. The local
  development default is `postgresql+psycopg:///telecom_db`.
- `TEST_DATABASE_URL` is required by database integration tests and must resolve
  to a PostgreSQL database named exactly `telecom_test_db`.
- `backend/tests/db_safety.py` validates both the URL and PostgreSQL's
  `current_database()` response before a test can write.
- No command in this workflow drops, resets, truncates, or recreates a database.

Create `telecom_test_db` separately if it does not already exist. Database
provisioning and permissions are administrator responsibilities and are not
automated by the test suite.

## Apply migrations to the isolated test database

```bash
DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run alembic upgrade head
```

This changes only `telecom_test_db`. On 2026-10-25 the command completed with
PostgreSQL transactional DDL and placed the database at revision
`926cf9047962`.

## Run all backend tests

```bash
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run pytest backend/tests -q
```

Verified result on 2026-10-25: **29 passed in 0.38s**. The eight PostgreSQL
tests cover the safety connection, transaction rollback, uniqueness, foreign
keys, check constraints, seed contents, and repeatable seeding. Test writes are
rolled back; expected constraint failures run inside savepoints so they do not
invalidate the enclosing cleanup transaction.

Running the suite without `TEST_DATABASE_URL` deliberately fails the database
tests before connecting. This is a safety feature, not a supported shortcut.

## Load fictional seed data

```bash
uv run python -m backend.app.db.seed
```

The loader reads `DATABASE_URL`, performs one atomic transaction, and reports
the managed record counts. It upserts fixed customer, plan, and ticket natural
keys and detects the fixed subscriptions and ticket events before inserting.
Rerunning it updates/reuses its own records without deleting any records or
resetting the database.

To exercise the command against the isolated database rather than development:

```bash
DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run python -m backend.app.db.seed
```

Only fictional identities and reserved `.test` email addresses are included.

## Ruff checks

```bash
uv run ruff check backend
uv run ruff format --check backend
```

Verified on 2026-10-25: lint passed and all **55 backend Python files** were
formatted. In the managed execution environment, the installed `.venv/bin/ruff`
entry point was used after `uv run` could not initialize its cache; this did not
change the tool version or check scope.

## Alembic consistency checks

```bash
DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run alembic current
DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run alembic heads
DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run alembic check
```

Verified on 2026-10-25:

- current: `926cf9047962 (head)`
- heads: `926cf9047962 (head)`
- check: `No new upgrade operations detected.`

These checks do not perform a destructive downgrade. Migration downgrade and
upgrade lifecycle testing uses a separate guard:

```bash
MIGRATION_TEST_DATABASE_URL=postgresql+psycopg:///telecom_migration_test_db \
ALLOW_DISPOSABLE_DB_TEST=yes \
uv run python -m backend.scripts.verify_migration_cycle
```

The runner rejects every other database name. On 2026-10-25 an explicitly
approved disposable database completed upgrade → downgrade to base → upgrade →
Alembic consistency check and was then deleted. Never point this command at
`telecom_db` or `telecom_test_db`.

## Least-privilege runtime role

`docs/db/postgresql-runtime-role.sql` is an administrator-run, credential-free
template. It accepts the role name and password as psql variables, denies
superuser/database/role creation, grants data access and sequence usage, and
revokes schema creation. Migration credentials remain separate. The repository
does not provision or store the password automatically.
