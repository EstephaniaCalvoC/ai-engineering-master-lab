from functools import lru_cache

from arize.otel import Endpoint, register
from openinference.instrumentation import OITracer, TraceConfig
from openinference.instrumentation.anthropic import AnthropicInstrumentor
from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.env import ENV_FILE
from app.config.logger import get_logger

logger = get_logger(__name__)

_tracer_provider: TracerProvider | None = None


class TracingSettings(BaseSettings):
    # hide_input_in_errors keeps an API key out of validation errors
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, extra="ignore", hide_input_in_errors=True
    )

    TRACING_ENABLED: bool = True
    ARIZE_SPACE_ID: str | None = None
    ARIZE_API_KEY: SecretStr | None = None
    ARIZE_PROJECT_NAME: str = "estimator-cag"
    ARIZE_COLLECTOR_ENDPOINT: str = Endpoint.ARIZE

    @field_validator("ARIZE_SPACE_ID", "ARIZE_API_KEY", mode="before")
    @classmethod
    def empty_to_none(cls, value):
        # An empty value in .env means "not set"
        return None if value == "" else value

    @property
    def is_configured(self) -> bool:
        return bool(
            self.TRACING_ENABLED
            and self.ARIZE_SPACE_ID
            and self.ARIZE_API_KEY
            and self.ARIZE_API_KEY.get_secret_value()
        )


@lru_cache
def get_tracing_settings() -> TracingSettings:
    return TracingSettings()


def configure_tracing() -> TracerProvider | None:
    """Register the Arize AX tracer provider and instrument LLM SDKs.

    Must run before any LLM client is instantiated. Returns None without
    registering when tracing is disabled or Arize credentials are not set.
    """
    global _tracer_provider
    if _tracer_provider is not None:
        return _tracer_provider

    settings = get_tracing_settings()
    if not settings.is_configured:
        logger.debug(
            "Arize tracing not configured (TRACING_ENABLED=%s, space_id_set=%s, api_key_set=%s)",
            settings.TRACING_ENABLED,
            bool(settings.ARIZE_SPACE_ID),
            bool(settings.ARIZE_API_KEY and settings.ARIZE_API_KEY.get_secret_value()),
        )
        return None

    assert settings.ARIZE_SPACE_ID is not None
    assert settings.ARIZE_API_KEY is not None

    tracer_provider = register(
        space_id=settings.ARIZE_SPACE_ID,
        api_key=settings.ARIZE_API_KEY.get_secret_value(),
        project_name=settings.ARIZE_PROJECT_NAME,
        endpoint=settings.ARIZE_COLLECTOR_ENDPOINT,
    )
    AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)
    OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

    _tracer_provider = tracer_provider
    logger.info(
        "Arize AX tracing configured for project '%s' (%s)",
        settings.ARIZE_PROJECT_NAME,
        settings.ARIZE_COLLECTOR_ENDPOINT,
    )
    return tracer_provider


def shutdown_tracing() -> None:
    """Flush buffered spans and shut down the active tracer provider."""
    global _tracer_provider
    if _tracer_provider is None:
        return
    _tracer_provider.force_flush()
    _tracer_provider.shutdown()
    _tracer_provider = None


def get_tracer(name: str) -> OITracer:
    """Return an OpenInference tracer backed by the global OpenTelemetry provider."""
    return OITracer(trace.get_tracer(name), config=TraceConfig())
