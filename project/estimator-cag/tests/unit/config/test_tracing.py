from types import SimpleNamespace

import pytest

from app.config import TracingSettings, get_tracing_settings
from app.config import tracing as tracing_module


@pytest.fixture(autouse=True)
def reset_tracing_provider(monkeypatch):
    monkeypatch.setattr(tracing_module, "_tracer_provider", None)


def test_defaults_when_no_env_is_set():
    settings = TracingSettings()

    assert settings.TRACING_ENABLED is True
    assert settings.ARIZE_SPACE_ID is None
    assert settings.ARIZE_API_KEY is None
    assert settings.ARIZE_PROJECT_NAME == "estimator-cag"
    assert settings.ARIZE_COLLECTOR_ENDPOINT == "https://otlp.arize.com/v1"
    assert settings.is_configured is False


def test_empty_credentials_are_treated_as_unset(monkeypatch):
    monkeypatch.setenv("ARIZE_SPACE_ID", "")
    monkeypatch.setenv("ARIZE_API_KEY", "")

    settings = TracingSettings()

    assert settings.ARIZE_SPACE_ID is None
    assert settings.ARIZE_API_KEY is None
    assert settings.is_configured is False


def test_values_are_read_from_env(monkeypatch):
    monkeypatch.setenv("TRACING_ENABLED", "true")
    monkeypatch.setenv("ARIZE_SPACE_ID", "U3BhY2U6MTIz")
    monkeypatch.setenv("ARIZE_API_KEY", "ak-test-key")
    monkeypatch.setenv("ARIZE_PROJECT_NAME", "custom-project")
    monkeypatch.setenv(
        "ARIZE_COLLECTOR_ENDPOINT", "https://otlp.eu-west-1a.arize.com/v1"
    )

    settings = TracingSettings()

    assert settings.is_configured is True
    assert settings.ARIZE_SPACE_ID == "U3BhY2U6MTIz"
    assert settings.ARIZE_API_KEY is not None
    assert settings.ARIZE_API_KEY.get_secret_value() == "ak-test-key"
    assert settings.ARIZE_PROJECT_NAME == "custom-project"
    assert settings.ARIZE_COLLECTOR_ENDPOINT == "https://otlp.eu-west-1a.arize.com/v1"


def test_configure_tracing_skips_when_unconfigured(monkeypatch):
    called = False

    def fake_register(**kwargs):
        nonlocal called
        called = True
        return SimpleNamespace()

    monkeypatch.setattr(tracing_module, "register", fake_register)

    provider = tracing_module.configure_tracing()

    assert provider is None
    assert called is False


def test_configure_tracing_registers_and_instruments_both_providers(monkeypatch):
    monkeypatch.setenv("ARIZE_SPACE_ID", "U3BhY2U6MTIz")
    monkeypatch.setenv("ARIZE_API_KEY", "ak-test-key")
    get_tracing_settings.cache_clear()

    register_calls = []
    instrument_calls = []
    flushed = []
    shut_down = []

    fake_provider = SimpleNamespace(
        force_flush=lambda: flushed.append(True),
        shutdown=lambda: shut_down.append(True),
    )

    def fake_register(**kwargs):
        register_calls.append(kwargs)
        return fake_provider

    class FakeInstrumentor:
        def __init__(self, name):
            self.name = name

        def instrument(self, *, tracer_provider):
            instrument_calls.append((self.name, tracer_provider))

    monkeypatch.setattr(tracing_module, "register", fake_register)
    monkeypatch.setattr(
        tracing_module,
        "AnthropicInstrumentor",
        lambda: FakeInstrumentor("anthropic"),
    )
    monkeypatch.setattr(
        tracing_module,
        "OpenAIInstrumentor",
        lambda: FakeInstrumentor("openai"),
    )

    provider = tracing_module.configure_tracing()
    # Second call should be a no-op returning the same provider
    provider_again = tracing_module.configure_tracing()

    assert provider is fake_provider
    assert provider_again is fake_provider
    assert register_calls == [
        {
            "space_id": "U3BhY2U6MTIz",
            "api_key": "ak-test-key",
            "project_name": "estimator-cag",
            "endpoint": "https://otlp.arize.com/v1",
        }
    ]
    assert instrument_calls == [
        ("anthropic", fake_provider),
        ("openai", fake_provider),
    ]

    tracing_module.shutdown_tracing()
    assert flushed == [True]
    assert shut_down == [True]
