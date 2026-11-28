from typing import get_args

import pytest

from app.config.service import LLMProviderName
from app.services.llm import build_adapter
from app.services.llm.anthropic_adapter import AnthropicAdapter
from app.services.llm.factory import _ADAPTERS
from app.services.llm.openai_adapter import OpenAIAdapter


def test_build_adapter_returns_adapter_for_each_provider():
    anthropic = build_adapter("anthropic", "claude-sonnet-5-5", "test-key", 16_000)
    openai = build_adapter("openai", "gpt-4o", "test-key", 8_000, max_retries=0)

    assert isinstance(anthropic, AnthropicAdapter)
    assert anthropic.model == "claude-sonnet-5-5"
    assert anthropic.max_output_tokens == 16_000
    assert anthropic.max_retries == 2
    assert isinstance(openai, OpenAIAdapter)
    assert openai.model == "gpt-4o"
    assert openai.max_output_tokens == 8_000
    assert openai.max_retries == 0


def test_build_adapter_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported LLM provider: gemini"):
        build_adapter("gemini", "some-model", "test-key", 16_000)


def test_adapter_registry_matches_settings_provider_names():
    # Every provider allowed in settings needs an adapter, and no adapter may be unlisted.
    assert set(_ADAPTERS) == set(get_args(LLMProviderName))
