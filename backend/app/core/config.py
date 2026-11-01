from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with environment validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        secrets_dir="/run/secrets" if Path("/run/secrets").is_dir() else None,
        extra="ignore",
    )

    app_name: str = "Telecom Agentic AI Support Platform"
    app_env: Literal["development", "testing", "production"] = "development"
    app_debug: bool = False

    api_v1_prefix: str = "/api/v1"

    backend_host: str = "127.0.0.1"
    backend_port: int = Field(default=8000, ge=1, le=65535)

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    database_url: str = "postgresql+psycopg:///telecom_db"
    database_password_file: Path | None = None

    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_api_key: SecretStr | None = None
    qdrant_collection: str = "telecom_knowledge"
    embedding_dimensions: int = Field(default=384, ge=64, le=4096)
    retrieval_min_score: float = Field(default=0.03, ge=0.0, le=1.0)

    auth_jwt_secret: SecretStr | None = None
    auth_jwt_audience: str = "telecom-agentic-ai-support"
    entra_tenant_id: str | None = None
    entra_client_id: str | None = None
    entra_client_secret: SecretStr | None = None
    entra_client_secret_file: Path | None = None
    entra_redirect_uri: str = "http://localhost:8000/auth/callback"
    frontend_url: str = "http://localhost:5173"
    session_cookie_name: str = "signaldesk_session"
    session_ttl_minutes: int = Field(default=480, ge=5, le=1440)
    cookie_secure: bool = False

    deep_agent_model: str | None = None
    openai_api_key: SecretStr | None = None
    deep_agent_max_steps: int = Field(default=8, ge=2, le=30)
    deep_agent_max_tool_calls: int = Field(default=6, ge=1, le=20)
    deep_agent_timeout_seconds: float = Field(default=20.0, gt=0, le=120)

    @model_validator(mode="after")
    def apply_database_password_file(self) -> "Settings":
        """Add a runtime-mounted password without placing it in Compose output."""

        if self.database_password_file is None:
            return self
        password = self.database_password_file.read_text(encoding="utf-8").strip()
        if not password:
            raise ValueError("database password file is empty")
        marker = "postgresql+psycopg://telecom@"
        if self.database_url.startswith(marker):
            self.database_url = self.database_url.replace(
                marker,
                f"postgresql+psycopg://telecom:{quote(password, safe='')}@",
                1,
            )
        return self

    @model_validator(mode="after")
    def apply_entra_secret_file(self) -> "Settings":
        """Load the Entra secret from a mounted file without exposing its value."""

        if self.entra_client_secret_file is None:
            return self
        secret = self.entra_client_secret_file.read_text(encoding="utf-8").strip()
        if not secret:
            raise ValueError("Entra client secret file is empty")
        self.entra_client_secret = SecretStr(secret)
        return self

    @model_validator(mode="after")
    def require_secure_production_cookies(self) -> "Settings":
        if self.app_env == "production" and not self.cookie_secure:
            raise ValueError("COOKIE_SECURE must be true in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Create and cache application settings."""
    return Settings()
