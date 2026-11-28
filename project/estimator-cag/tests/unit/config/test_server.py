import pytest
from pydantic import ValidationError

from app.config import ServerSettings, get_server_settings


def test_defaults_when_no_env_is_set():
    settings = ServerSettings()

    assert settings.APP_ENV == "development"
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.HOST == "127.0.0.1"
    assert settings.PORT == 8001


def test_values_are_read_from_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9000")

    settings = ServerSettings()

    assert settings.APP_ENV == "production"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 9000


def test_app_env_only_accepts_development_or_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")

    with pytest.raises(ValidationError):
        ServerSettings()


def test_get_server_settings_returns_cached_instance():
    assert get_server_settings() is get_server_settings()
