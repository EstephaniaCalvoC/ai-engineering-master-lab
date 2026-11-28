from functools import lru_cache
from typing import Literal

from pydantic import Field, PrivateAttr, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.env import ENV_FILE, ENV_VAR_NAME, read_env_var

# Providers the service has an adapter for. Keep in sync with app/services/llm/factory.py.
LLMProviderName = Literal["anthropic", "openai"]


class ServiceSettings(BaseSettings):
    # hide_input_in_errors keeps a pasted API key out of validation errors
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, extra="ignore", hide_input_in_errors=True
    )

    # Main LLM (required)
    MAIN_LLM_PROVIDER: LLMProviderName
    MAIN_LLM_MODEL: str
    # Name of the env var that holds the main provider's API key, e.g. ANTHROPIC_API_KEY
    MAIN_PROVIDER_API_KEY: str

    # Fallback LLM (optional; disabled when the provider is empty)
    FALLBACK_LLM_PROVIDER: LLMProviderName | None = None
    FALLBACK_LLM_MODEL: str | None = None
    # Name of the env var that holds the fallback provider's API key, e.g. OPENAI_API_KEY
    FALLBACK_PROVIDER_API_KEY: str | None = None

    # Allowed transcription length in characters (limits prompt size and cost)
    MIN_TRANSCRIPTION_LENGTH: int = Field(default=100, gt=0)
    MAX_TRANSCRIPTION_LENGTH: int = Field(default=20_000, gt=0)

    # Output ceiling per LLM reply, in tokens. Some OpenAI models reject values above 16384,
    # so the limit is 16000 and the default is the same.
    MAX_OUTPUT_TOKENS: int = Field(default=16_000, gt=0, le=16_000)

    # Number of automatic retries the provider SDK performs on transient errors (429, 5xx, timeouts).
    LLM_MAX_RETRIES: int = Field(default=2, ge=0)

    _main_api_key: SecretStr = PrivateAttr()
    _fallback_api_key: SecretStr | None = PrivateAttr(default=None)

    @field_validator(
        "FALLBACK_LLM_PROVIDER",
        "FALLBACK_LLM_MODEL",
        "FALLBACK_PROVIDER_API_KEY",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value):
        # An empty value in .env means "not set"
        return None if value == "" else value

    @field_validator("MAIN_PROVIDER_API_KEY", "FALLBACK_PROVIDER_API_KEY")
    @classmethod
    def must_name_an_env_var(cls, value):
        # Catch someone pasting the key itself instead of its variable name
        if value is not None and not ENV_VAR_NAME.fullmatch(value):
            raise ValueError(
                "must be the name of an environment variable, such as "
                "ANTHROPIC_API_KEY, not the API key itself"
            )
        return value

    @model_validator(mode="after")
    def validate_transcription_bounds(self):
        if self.MIN_TRANSCRIPTION_LENGTH > self.MAX_TRANSCRIPTION_LENGTH:
            raise ValueError(
                "MIN_TRANSCRIPTION_LENGTH must not be greater than MAX_TRANSCRIPTION_LENGTH"
            )
        return self

    @model_validator(mode="after")
    def validate_providers(self):
        if self.FALLBACK_LLM_PROVIDER:
            if not self.FALLBACK_LLM_MODEL:
                raise ValueError(
                    "FALLBACK_LLM_MODEL is required when FALLBACK_LLM_PROVIDER is set"
                )
            if not self.FALLBACK_PROVIDER_API_KEY:
                raise ValueError(
                    "FALLBACK_PROVIDER_API_KEY is required when FALLBACK_LLM_PROVIDER is set"
                )

        self._main_api_key = self._resolve_api_key(
            "MAIN_PROVIDER_API_KEY", self.MAIN_PROVIDER_API_KEY
        )
        if self.FALLBACK_LLM_PROVIDER:
            self._fallback_api_key = self._resolve_api_key(
                "FALLBACK_PROVIDER_API_KEY", self.FALLBACK_PROVIDER_API_KEY
            )
        return self

    @staticmethod
    def _resolve_api_key(field: str, var_name: str) -> SecretStr:
        value = read_env_var(var_name)
        if value is None:
            raise ValueError(
                f"{field} points to {var_name}, which is not set or is empty"
            )
        return SecretStr(value)

    @property
    def main_api_key(self) -> SecretStr:
        return self._main_api_key

    @property
    def fallback_api_key(self) -> SecretStr | None:
        return self._fallback_api_key


@lru_cache
def get_service_settings() -> ServiceSettings:
    return ServiceSettings()
