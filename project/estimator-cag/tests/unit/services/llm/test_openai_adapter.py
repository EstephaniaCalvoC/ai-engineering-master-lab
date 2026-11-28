import asyncio
from types import SimpleNamespace

import httpx
import openai
import pytest
from pydantic import ValidationError

from app.schemas.estimation import EstimationOutputData
from app.services.llm import (
    LLMInvalidResponse,
    LLMRateLimited,
    LLMResult,
    LLMUnavailable,
    openai_adapter,
)
from tests.helpers.llm import MAX_OUTPUT_TOKENS, make_openai_adapter, sample_estimate


def _httpx_response(status_code: int) -> httpx.Response:
    return httpx.Response(
        status_code, request=httpx.Request("POST", "https://api.openai.com")
    )


def parsed_reply(parsed=None, refusal=None):
    message = SimpleNamespace(parsed=parsed, refusal=refusal)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_openai_sends_model_limits_timeout_messages_and_schema(monkeypatch):
    captured = {}

    async def parse(**kwargs):
        captured.update(kwargs)
        return parsed_reply(parsed=sample_estimate())

    adapter = make_openai_adapter(monkeypatch, parse)

    asyncio.run(adapter.generate("system text", "A" * 120, EstimationOutputData))

    assert captured["model"] == "gpt-4o"
    assert captured["max_completion_tokens"] == MAX_OUTPUT_TOKENS
    assert captured["timeout"] == openai_adapter.OPENAI_TIMEOUT_SECONDS
    assert captured["response_format"] is EstimationOutputData
    assert captured["messages"] == [
        {"role": "system", "content": "system text"},
        {"role": "user", "content": "A" * 120},
    ]


def test_openai_returns_parsed_estimate(monkeypatch):
    async def parse(**kwargs):
        return parsed_reply(parsed=sample_estimate())

    adapter = make_openai_adapter(monkeypatch, parse)

    result = asyncio.run(adapter.generate("s", "u", EstimationOutputData))

    assert result == LLMResult(
        data=sample_estimate(), model="gpt-4o", provider="openai"
    )


@pytest.mark.parametrize("refusal", [None, "I can't help with that."])
def test_openai_without_parsed_output_raises_clear_error(monkeypatch, refusal):
    async def parse(**kwargs):
        return parsed_reply(parsed=None, refusal=refusal)

    adapter = make_openai_adapter(monkeypatch, parse)

    with pytest.raises(
        LLMInvalidResponse, match="did not return a structured estimate"
    ):
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))


def test_openai_refusal_text_is_included_in_error(monkeypatch):
    async def parse(**kwargs):
        return parsed_reply(parsed=None, refusal="I can't help with that.")

    adapter = make_openai_adapter(monkeypatch, parse)

    with pytest.raises(LLMInvalidResponse, match="I can't help with that."):
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))


def test_openai_empty_choices_raises_llm_invalid_response(monkeypatch):
    async def parse(**kwargs):
        return SimpleNamespace(choices=[])

    adapter = make_openai_adapter(monkeypatch, parse)

    with pytest.raises(LLMInvalidResponse, match="no choices"):
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))


def test_openai_rate_limit_error_maps_to_llm_rate_limited(monkeypatch):
    async def parse(**kwargs):
        raise openai.RateLimitError(
            "too many requests", response=_httpx_response(429), body=None
        )

    adapter = make_openai_adapter(monkeypatch, parse)

    with pytest.raises(LLMRateLimited) as exc_info:
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))

    assert isinstance(exc_info.value.__cause__, openai.RateLimitError)


@pytest.mark.parametrize(
    "sdk_error",
    [
        openai.APITimeoutError(request=httpx.Request("POST", "https://api.openai.com")),
        openai.APIConnectionError(
            request=httpx.Request("POST", "https://api.openai.com")
        ),
        openai.InternalServerError(
            "server error", response=_httpx_response(500), body=None
        ),
        openai.AuthenticationError(
            "invalid api key", response=_httpx_response(401), body=None
        ),
    ],
)
def test_openai_provider_errors_map_to_llm_unavailable(monkeypatch, sdk_error):
    async def parse(**kwargs):
        raise sdk_error

    adapter = make_openai_adapter(monkeypatch, parse)

    with pytest.raises(LLMUnavailable) as exc_info:
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))

    assert exc_info.value.__cause__ is sdk_error


@pytest.mark.parametrize(
    "sdk_error",
    [
        openai.LengthFinishReasonError(completion=SimpleNamespace(usage=None)),
        openai.ContentFilterFinishReasonError(),
        openai.APIResponseValidationError(response=_httpx_response(200), body=None),
        ValidationError.from_exception_data("EstimationOutputData", []),
    ],
)
def test_openai_invalid_response_errors_map_to_llm_invalid_response(
    monkeypatch, sdk_error
):
    async def parse(**kwargs):
        raise sdk_error

    adapter = make_openai_adapter(monkeypatch, parse)

    with pytest.raises(LLMInvalidResponse) as exc_info:
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))

    assert exc_info.value.__cause__ is sdk_error


def test_openai_uses_response_model_passed_by_caller(monkeypatch):
    from pydantic import BaseModel

    class Other(BaseModel):
        value: int

    captured = {}

    async def parse(**kwargs):
        captured.update(kwargs)
        return parsed_reply(parsed=Other(value=1))

    adapter = make_openai_adapter(monkeypatch, parse)

    result = asyncio.run(adapter.generate("s", "u", Other))

    assert captured["response_format"] is Other
    assert result.data == Other(value=1)


def test_openai_adapter_passes_max_retries_to_sdk_client(monkeypatch):
    captured = {}

    def fake_client(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(openai_adapter, "AsyncOpenAI", fake_client)

    default_adapter = openai_adapter.OpenAIAdapter(
        model="gpt-4o", api_key="test-key", max_output_tokens=MAX_OUTPUT_TOKENS
    )
    assert default_adapter.max_retries == 2
    assert captured["max_retries"] == 2

    custom_adapter = openai_adapter.OpenAIAdapter(
        model="gpt-4o",
        api_key="test-key",
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_retries=4,
    )
    assert custom_adapter.max_retries == 4
    assert captured["max_retries"] == 4
