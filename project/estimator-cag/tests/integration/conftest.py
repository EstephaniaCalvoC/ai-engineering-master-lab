import importlib
import sys

import pytest
from fastapi.testclient import TestClient

from app.config import (
    ServerSettings,
    ServiceSettings,
    get_server_settings,
    get_service_settings,
    get_tracing_settings,
)
from app.config.tracing import configure_tracing, shutdown_tracing

GETTERS = (get_server_settings, get_service_settings, get_tracing_settings)

# Default non-secret service settings used by make_client() when a test does not override them.
# API keys (e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY) come from tests/integration/.env.integration
# via `uv run --env-file tests/integration/.env.integration pytest tests/integration --run-integration`.
DEFAULT_SERVICE_ENV: dict[str, str] = {
    "MAIN_LLM_PROVIDER": "openai",
    "MAIN_LLM_MODEL": "gpt-4o",
    "MAIN_PROVIDER_API_KEY": "OPENAI_API_KEY",
}

SAMPLE_TRANSCRIPT = """
Client: a regional logistics company. They need a web portal for dispatchers to assign
deliveries to drivers. Dispatchers see a map of open orders and drag them onto a driver's
route. Drivers get a mobile-friendly view of their stops, with navigation links and a
button to confirm each delivery with a photo. Managers need a daily report of late
deliveries and driver utilisation, exported to CSV. Orders come from an existing ERP through
a nightly CSV import, and the portal must reject duplicate order numbers. Single sign-on
through the client's Azure Active Directory. Roughly 40 dispatchers and 300 drivers.
"""


@pytest.fixture
def sample_transcript() -> str:
    return SAMPLE_TRANSCRIPT


def _clear_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (*ServerSettings.model_fields, *ServiceSettings.model_fields):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def isolated_integration_env(monkeypatch, tmp_path):
    """Isolate each integration test from the repo's .env and non-secret shell vars.

    API keys loaded from tests/integration/.env.integration (such as OPENAI_API_KEY and
    ANTHROPIC_API_KEY) remain in the process environment, while ServerSettings and
    ServiceSettings fields are cleared so each test defines its own configuration.
    """
    monkeypatch.chdir(tmp_path)
    _clear_settings_env(monkeypatch)
    for getter in GETTERS:
        getter.cache_clear()
    yield
    for getter in GETTERS:
        getter.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def flush_tracing_after_integration_session():
    """Flush and shut down Arize tracing once all integration tests finish.

    make_client() returns TestClient(app) without entering FastAPI's lifespan,
    so buffered BatchSpanProcessor spans would otherwise be dropped on exit.
    """
    yield
    shutdown_tracing()


@pytest.fixture
def make_client(monkeypatch):
    """Build a TestClient with per-test service settings.

    Starts from DEFAULT_SERVICE_ENV and applies any keyword overrides. Pass None as a value
    to unset a variable. Reloads app.services.estimation so its module-level settings and
    LLM adapter are rebuilt from the new environment.
    """

    def _make_client(**env_overrides: str | int | None) -> TestClient:
        _clear_settings_env(monkeypatch)
        env: dict[str, str | int | None] = {**DEFAULT_SERVICE_ENV, **env_overrides}
        for key, value in env.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, str(value))

        for getter in GETTERS:
            getter.cache_clear()

        # Ensure tracing and OpenInference instrumentors are active before rebuilding
        # the LLM client, even if app.main was already imported in an unconfigured env.
        configure_tracing()

        if "app.services.estimation" in sys.modules:
            importlib.reload(sys.modules["app.services.estimation"])

        from app.main import app

        return TestClient(app)

    return _make_client
