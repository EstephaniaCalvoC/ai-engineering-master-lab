import pytest
from pydantic import ValidationError

from app.config import ServiceSettings, get_service_settings


def test_main_llm_provider_and_model_are_required():
    with pytest.raises(ValidationError) as exc:
        ServiceSettings()

    missing = {error["loc"][0] for error in exc.value.errors()}
    assert missing == {"MAIN_LLM_PROVIDER", "MAIN_LLM_MODEL", "MAIN_PROVIDER_API_KEY"}


def test_defaults_when_only_required_values_are_set(main_llm):
    settings = ServiceSettings()

    assert settings.FALLBACK_LLM_PROVIDER is None
    assert settings.FALLBACK_LLM_MODEL is None
    assert settings.FALLBACK_PROVIDER_API_KEY is None
    assert settings.main_api_key.get_secret_value() == "sk-test-main"
    assert settings.fallback_api_key is None


def test_key_is_read_from_dotenv_when_not_in_process_env(
    main_llm, monkeypatch, tmp_path
):
    monkeypatch.delenv("TEST_MAIN_API_KEY")
    (tmp_path / ".env").write_text("TEST_MAIN_API_KEY=sk-from-dotenv\n")

    assert ServiceSettings().main_api_key.get_secret_value() == "sk-from-dotenv"


def test_process_env_takes_precedence_over_dotenv(main_llm, monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("TEST_MAIN_API_KEY=sk-from-dotenv\n")
    monkeypatch.setenv("TEST_MAIN_API_KEY", "sk-from-env")

    assert ServiceSettings().main_api_key.get_secret_value() == "sk-from-env"


def test_main_key_reference_to_unset_variable_is_rejected(main_llm, monkeypatch):
    monkeypatch.delenv("TEST_MAIN_API_KEY")

    with pytest.raises(ValidationError, match="TEST_MAIN_API_KEY, which is not set"):
        ServiceSettings()


def test_main_key_reference_to_empty_variable_is_rejected(main_llm, monkeypatch):
    monkeypatch.setenv("TEST_MAIN_API_KEY", "")

    with pytest.raises(ValidationError, match="TEST_MAIN_API_KEY, which is not set"):
        ServiceSettings()


def test_empty_main_key_reference_is_rejected(main_llm, monkeypatch):
    monkeypatch.setenv("MAIN_PROVIDER_API_KEY", "")

    with pytest.raises(ValidationError) as exc:
        ServiceSettings()

    assert {error["loc"][0] for error in exc.value.errors()} == {
        "MAIN_PROVIDER_API_KEY"
    }


def test_pasted_api_key_is_rejected_without_echoing_it(main_llm, monkeypatch):
    pasted = "sk-ant-api03-not-a-real-key"
    monkeypatch.setenv("MAIN_PROVIDER_API_KEY", pasted)

    with pytest.raises(ValidationError) as exc:
        ServiceSettings()

    assert "not the API key itself" in str(exc.value)
    assert pasted not in str(exc.value)


def test_fallback_provider_requires_fallback_model(main_llm, monkeypatch):
    monkeypatch.setenv("FALLBACK_LLM_PROVIDER", "openai")

    with pytest.raises(ValidationError, match="FALLBACK_LLM_MODEL is required"):
        ServiceSettings()


def test_fallback_provider_requires_fallback_key_reference(main_llm, monkeypatch):
    monkeypatch.setenv("FALLBACK_LLM_PROVIDER", "openai")
    monkeypatch.setenv("FALLBACK_LLM_MODEL", "gpt-4o")

    with pytest.raises(ValidationError, match="FALLBACK_PROVIDER_API_KEY is required"):
        ServiceSettings()


def test_fallback_provider_and_model_together_are_accepted(main_llm, monkeypatch):
    monkeypatch.setenv("FALLBACK_LLM_PROVIDER", "openai")
    monkeypatch.setenv("FALLBACK_LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("FALLBACK_PROVIDER_API_KEY", "TEST_FALLBACK_API_KEY")
    monkeypatch.setenv("TEST_FALLBACK_API_KEY", "sk-test-fallback")

    settings = ServiceSettings()

    assert settings.FALLBACK_LLM_PROVIDER == "openai"
    assert settings.FALLBACK_LLM_MODEL == "gpt-4o"
    assert settings.fallback_api_key.get_secret_value() == "sk-test-fallback"


def test_fallback_key_reference_to_unset_variable_is_rejected(main_llm, monkeypatch):
    monkeypatch.setenv("FALLBACK_LLM_PROVIDER", "openai")
    monkeypatch.setenv("FALLBACK_LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("FALLBACK_PROVIDER_API_KEY", "TEST_FALLBACK_API_KEY")

    with pytest.raises(
        ValidationError, match="TEST_FALLBACK_API_KEY, which is not set"
    ):
        ServiceSettings()


def test_empty_fallback_values_disable_the_fallback(main_llm, monkeypatch):
    monkeypatch.setenv("FALLBACK_LLM_PROVIDER", "")
    monkeypatch.setenv("FALLBACK_LLM_MODEL", "")
    monkeypatch.setenv("FALLBACK_PROVIDER_API_KEY", "")

    settings = ServiceSettings()

    assert settings.FALLBACK_LLM_PROVIDER is None
    assert settings.FALLBACK_LLM_MODEL is None
    assert settings.FALLBACK_PROVIDER_API_KEY is None
    assert settings.fallback_api_key is None


def test_empty_fallback_model_with_provider_is_rejected(main_llm, monkeypatch):
    monkeypatch.setenv("FALLBACK_LLM_PROVIDER", "openai")
    monkeypatch.setenv("FALLBACK_LLM_MODEL", "")

    with pytest.raises(ValidationError, match="FALLBACK_LLM_MODEL is required"):
        ServiceSettings()


def test_api_keys_are_masked_in_repr(main_llm, monkeypatch):
    secret = "sk-test-not-a-real-key"
    monkeypatch.setenv("TEST_MAIN_API_KEY", secret)

    settings = ServiceSettings()

    assert settings.main_api_key.get_secret_value() == secret
    assert secret not in repr(settings)
    assert secret not in str(settings)


def test_get_service_settings_returns_cached_instance(main_llm):
    assert get_service_settings() is get_service_settings()


def test_transcription_length_bounds_have_defaults(main_llm):
    settings = ServiceSettings()

    assert settings.MIN_TRANSCRIPTION_LENGTH == 100
    assert settings.MAX_TRANSCRIPTION_LENGTH == 20_000


def test_transcription_length_bounds_can_be_overridden(main_llm, monkeypatch):
    monkeypatch.setenv("MIN_TRANSCRIPTION_LENGTH", "10")
    monkeypatch.setenv("MAX_TRANSCRIPTION_LENGTH", "5000")

    settings = ServiceSettings()

    assert settings.MIN_TRANSCRIPTION_LENGTH == 10
    assert settings.MAX_TRANSCRIPTION_LENGTH == 5000


def test_min_transcription_length_above_max_is_rejected(main_llm, monkeypatch):
    monkeypatch.setenv("MIN_TRANSCRIPTION_LENGTH", "600")
    monkeypatch.setenv("MAX_TRANSCRIPTION_LENGTH", "500")

    with pytest.raises(ValidationError, match="must not be greater than"):
        ServiceSettings()


def test_transcription_length_bounds_must_be_positive(main_llm, monkeypatch):
    monkeypatch.setenv("MAX_TRANSCRIPTION_LENGTH", "0")

    with pytest.raises(ValidationError) as exc:
        ServiceSettings()

    assert {error["loc"][0] for error in exc.value.errors()} == {
        "MAX_TRANSCRIPTION_LENGTH"
    }


def test_max_output_tokens_defaults_to_16000(main_llm):
    assert ServiceSettings().MAX_OUTPUT_TOKENS == 16_000


@pytest.mark.parametrize("value", ["1", "8000", "16000"])
def test_max_output_tokens_accepts_values_up_to_16000(main_llm, monkeypatch, value):
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", value)

    assert ServiceSettings().MAX_OUTPUT_TOKENS == int(value)


@pytest.mark.parametrize("value", ["16001", "20000", "0", "-1"])
def test_max_output_tokens_above_16000_or_not_positive_is_rejected(
    main_llm, monkeypatch, value
):
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", value)

    with pytest.raises(ValidationError) as exc:
        ServiceSettings()

    assert {error["loc"][0] for error in exc.value.errors()} == {"MAX_OUTPUT_TOKENS"}


@pytest.mark.parametrize("provider", ["anthropic", "openai"])
def test_supported_main_providers_are_accepted(main_llm, monkeypatch, provider):
    monkeypatch.setenv("MAIN_LLM_PROVIDER", provider)

    assert ServiceSettings().MAIN_LLM_PROVIDER == provider


@pytest.mark.parametrize("provider", ["gemini", "Anthropic", "azure"])
def test_unsupported_main_provider_is_rejected(main_llm, monkeypatch, provider):
    monkeypatch.setenv("MAIN_LLM_PROVIDER", provider)

    with pytest.raises(ValidationError) as exc:
        ServiceSettings()

    assert {error["loc"][0] for error in exc.value.errors()} == {"MAIN_LLM_PROVIDER"}


def test_unsupported_fallback_provider_is_rejected(main_llm, monkeypatch):
    monkeypatch.setenv("FALLBACK_LLM_PROVIDER", "gemini")
    monkeypatch.setenv("FALLBACK_LLM_MODEL", "some-model")
    monkeypatch.setenv("FALLBACK_PROVIDER_API_KEY", "TEST_FALLBACK_API_KEY")
    monkeypatch.setenv("TEST_FALLBACK_API_KEY", "sk-test-fallback")

    with pytest.raises(ValidationError) as exc:
        ServiceSettings()

    assert {error["loc"][0] for error in exc.value.errors()} == {
        "FALLBACK_LLM_PROVIDER"
    }


def test_llm_max_retries_defaults_to_2(main_llm):
    assert ServiceSettings().LLM_MAX_RETRIES == 2


@pytest.mark.parametrize("value", ["0", "2", "5"])
def test_llm_max_retries_can_be_overridden(main_llm, monkeypatch, value):
    monkeypatch.setenv("LLM_MAX_RETRIES", value)

    assert ServiceSettings().LLM_MAX_RETRIES == int(value)


def test_negative_llm_max_retries_is_rejected(main_llm, monkeypatch):
    monkeypatch.setenv("LLM_MAX_RETRIES", "-1")

    with pytest.raises(ValidationError) as exc:
        ServiceSettings()

    assert {error["loc"][0] for error in exc.value.errors()} == {"LLM_MAX_RETRIES"}
