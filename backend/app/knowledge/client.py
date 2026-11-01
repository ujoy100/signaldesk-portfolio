"""Qdrant client construction from application settings."""

from qdrant_client import QdrantClient

from backend.app.core.config import Settings, get_settings


def create_qdrant_client(settings: Settings | None = None) -> QdrantClient:
    """Create a Qdrant client without logging or persisting credentials."""

    resolved = settings or get_settings()
    api_key = (
        resolved.qdrant_api_key.get_secret_value() if resolved.qdrant_api_key else None
    )
    if resolved.qdrant_url == ":memory:":
        return QdrantClient(location=":memory:")
    return QdrantClient(url=resolved.qdrant_url, api_key=api_key)
