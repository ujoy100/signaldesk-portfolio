import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings, get_settings
from backend.app.main import create_app


@pytest.fixture
def clean_settings_environment(monkeypatch):
    """Remove relevant environment overrides for predictable tests."""
    setting_names = (
        "APP_NAME",
        "APP_ENV",
        "APP_DEBUG",
        "API_V1_PREFIX",
        "BACKEND_HOST",
        "BACKEND_PORT",
        "CORS_ORIGINS",
    )

    for name in setting_names:
        monkeypatch.delenv(name, raising=False)

    get_settings.cache_clear()

    yield

    get_settings.cache_clear()


def test_default_settings(clean_settings_environment):
    settings = Settings(_env_file=None)

    assert settings.app_name == "Telecom Agentic AI Support Platform"
    assert settings.app_env == "development"
    assert settings.app_debug is False
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.backend_host == "127.0.0.1"
    assert settings.backend_port == 8000
    assert settings.cors_origins == ["http://localhost:5173"]


def test_environment_variable_overrides(
    clean_settings_environment,
    monkeypatch,
):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("BACKEND_PORT", "9000")
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        '["http://localhost:3000"]',
    )

    settings = Settings(_env_file=None)

    assert settings.app_env == "testing"
    assert settings.backend_port == 9000
    assert settings.app_debug is True
    assert settings.cors_origins == ["http://localhost:3000"]


def test_custom_settings_injected_into_app(clean_settings_environment):
    settings = Settings(
        _env_file=None,
        app_name="Telecom Test Application",
        app_env="testing",
        app_debug=True,
    )

    app = create_app(settings=settings)

    assert app.title == "Telecom Test Application"
    assert app.debug is True
    assert app.state.settings is settings


@pytest.mark.parametrize(
    "invalid_port",
    [0, -1, 65536, 70000],
)
def test_invalid_backend_port_is_rejected(
    clean_settings_environment,
    invalid_port,
):
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,
            backend_port=invalid_port,
        )

    errors = exc_info.value.errors()

    assert any(error["loc"] == ("backend_port",) for error in errors)


@pytest.mark.parametrize(
    "invalid_env",
    ["invalid", "staging", "Development", ""],
)
def test_invalid_app_environment_is_rejected(
    clean_settings_environment,
    invalid_env,
):
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,
            app_env=invalid_env,
        )

    errors = exc_info.value.errors()

    assert any(error["loc"] == ("app_env",) for error in errors)
