import pytest

from app.config import (
    ServerSettings,
    ServiceSettings,
    TracingSettings,
    get_server_settings,
    get_service_settings,
    get_tracing_settings,
)

KEY_VARS = ("TEST_MAIN_API_KEY", "TEST_FALLBACK_API_KEY")
GETTERS = (get_server_settings, get_service_settings, get_tracing_settings)


@pytest.fixture
def main_llm(monkeypatch):
    # Valid main-LLM settings with a fake key, so settings load without a real .env
    monkeypatch.setenv("MAIN_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("MAIN_LLM_MODEL", "claude-sonnet-5-5")
    monkeypatch.setenv("MAIN_PROVIDER_API_KEY", "TEST_MAIN_API_KEY")
    monkeypatch.setenv("TEST_MAIN_API_KEY", "sk-test-main")
    get_service_settings.cache_clear()


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    # Run each test from an empty temp dir so the real .env is never read,
    # and remove any settings variables inherited from the host shell.
    monkeypatch.chdir(tmp_path)
    for name in (
        *ServerSettings.model_fields,
        *ServiceSettings.model_fields,
        *TracingSettings.model_fields,
        *KEY_VARS,
    ):
        monkeypatch.delenv(name, raising=False)
    for getter in GETTERS:
        getter.cache_clear()
    yield
    for getter in GETTERS:
        getter.cache_clear()
