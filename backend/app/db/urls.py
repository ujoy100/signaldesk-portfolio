"""Safe database URL conversions for drivers outside SQLAlchemy."""

from sqlalchemy.engine import URL, make_url


def postgres_checkpoint_url(database_url: str | URL) -> str:
    """Return a credential-preserving PostgreSQL URI for checkpoint savers."""

    url = make_url(database_url) if isinstance(database_url, str) else database_url
    if url.get_backend_name() != "postgresql":
        raise ValueError("Checkpoint storage requires PostgreSQL")
    return url.set(drivername="postgresql").render_as_string(hide_password=False)
