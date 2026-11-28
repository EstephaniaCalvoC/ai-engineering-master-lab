import asyncio
from types import SimpleNamespace

import anthropic
import httpx
import pytest
from pydantic import ValidationError

from app.schemas.estimation import EstimationOutputData
from app.services.llm import (
    LLMInvalidResponse,
    LLMRateLimited,
    LLMResult,
    LLMUnavailable,
)
from tests.helpers.llm import MAX_OUTPUT_TOKENS, make_anthropic_adapter, sample_estimate


def _httpx_response(status_code: int) -> httpx.Response:
    return httpx.Response(
        status_code, request=httpx.Request("POST", "https://api.anthropic.com")
    )


def parsed_reply(parsed=None, stop_reason="end_turn"):
    block = SimpleNamespace(type="text", text="{}", parsed_output=parsed)
    return SimpleNamespace(content=[block], stop_reason=stop_reason)


def test_anthropic_requests_structured_output_with_response_model(monkeypatch):
    captured = {}

    async def parse(**kwargs):
        captured.update(kwargs)
        return parsed_reply(parsed=sample_estimate())

    adapter = make_anthropic_adapter(monkeypatch, parse)

    asyncio.run(adapter.generate("system text", "A" * 120, EstimationOutputData))

    assert captured["model"] == "claude-sonnet-5-5"
    assert captured["max_tokens"] == MAX_OUTPUT_TOKENS
    assert captured["system"] == "system text"
    assert captured["messages"] == [{"role": "user", "content": "A" * 120}]
    # The schema goes through output_format, which the SDK sends as output_config.format.
    # No tool is involved.
    assert captured["output_format"] is EstimationOutputData
    assert "tools" not in captured
    assert "tool_choice" not in captured


def test_anthropic_returns_parsed_estimate(monkeypatch):
    async def parse(**kwargs):
        return parsed_reply(parsed=sample_estimate())

    adapter = make_anthropic_adapter(monkeypatch, parse)

    result = asyncio.run(adapter.generate("s", "u", EstimationOutputData))

    assert result == LLMResult(
        data=sample_estimate(), model="claude-sonnet-5-5", provider="anthropic"
    )
    assert isinstance(result.data, EstimationOutputData)
    assert result.data.total_hours == 120


def test_anthropic_reads_parsed_output_from_text_block(monkeypatch):
    async def parse(**kwargs):
        blocks = [
            SimpleNamespace(type="thinking", thinking="notes"),
            SimpleNamespace(type="text", text="{}", parsed_output=sample_estimate()),
        ]
        return SimpleNamespace(content=blocks, stop_reason="end_turn")

    adapter = make_anthropic_adapter(monkeypatch, parse)

    result = asyncio.run(adapter.generate("s", "u", EstimationOutputData))

    assert result.data == sample_estimate()


@pytest.mark.parametrize(
    "reply",
    [
        SimpleNamespace(content=[], stop_reason="end_turn"),
        parsed_reply(parsed=None, stop_reason="refusal"),
    ],
)
def test_anthropic_without_structured_output_raises_clear_error(monkeypatch, reply):
    async def parse(**kwargs):
        return reply

    adapter = make_anthropic_adapter(monkeypatch, parse)

    with pytest.raises(
        LLMInvalidResponse, match="did not return a structured estimate"
    ):
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))


def test_anthropic_truncated_reply_raises_clear_error(monkeypatch):
    async def parse(**kwargs):
        return parsed_reply(parsed=None, stop_reason="max_tokens")

    adapter = make_anthropic_adapter(monkeypatch, parse)

    with pytest.raises(LLMInvalidResponse, match="cut off at max_tokens"):
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))


def test_anthropic_invalid_reply_raises_llm_invalid_response(monkeypatch):
    async def parse(**kwargs):
        # The SDK validates the reply against the response model and raises on mismatch
        raise ValidationError.from_exception_data("EstimationOutputData", [])

    adapter = make_anthropic_adapter(monkeypatch, parse)

    with pytest.raises(LLMInvalidResponse) as exc_info:
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))

    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_anthropic_rate_limit_error_maps_to_llm_rate_limited(monkeypatch):
    async def parse(**kwargs):
        raise anthropic.RateLimitError(
            "too many requests", response=_httpx_response(429), body=None
        )

    adapter = make_anthropic_adapter(monkeypatch, parse)

    with pytest.raises(LLMRateLimited) as exc_info:
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))

    assert isinstance(exc_info.value.__cause__, anthropic.RateLimitError)


@pytest.mark.parametrize(
    "sdk_error",
    [
        anthropic.APITimeoutError(
            request=httpx.Request("POST", "https://api.anthropic.com")
        ),
        anthropic.APIConnectionError(
            request=httpx.Request("POST", "https://api.anthropic.com")
        ),
        anthropic.InternalServerError(
            "server error", response=_httpx_response(500), body=None
        ),
        anthropic.AuthenticationError(
            "invalid api key", response=_httpx_response(401), body=None
        ),
    ],
)
def test_anthropic_provider_errors_map_to_llm_unavailable(monkeypatch, sdk_error):
    async def parse(**kwargs):
        raise sdk_error

    adapter = make_anthropic_adapter(monkeypatch, parse)

    with pytest.raises(LLMUnavailable) as exc_info:
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))

    assert exc_info.value.__cause__ is sdk_error


def test_anthropic_response_validation_error_maps_to_llm_invalid_response(monkeypatch):
    async def parse(**kwargs):
        raise anthropic.APIResponseValidationError(
            response=_httpx_response(200), body=None
        )

    adapter = make_anthropic_adapter(monkeypatch, parse)

    with pytest.raises(LLMInvalidResponse) as exc_info:
        asyncio.run(adapter.generate("s", "u", EstimationOutputData))

    assert isinstance(exc_info.value.__cause__, anthropic.APIResponseValidationError)


def test_anthropic_adapter_passes_max_retries_to_sdk_client(monkeypatch):
    from app.services.llm import anthropic_adapter

    captured = {}

    def fake_client(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(anthropic_adapter, "AsyncAnthropic", fake_client)

    default_adapter = anthropic_adapter.AnthropicAdapter(
        model="claude-sonnet-5-5",
        api_key="test-key",
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
    assert default_adapter.max_retries == 2
    assert captured["max_retries"] == 2
    assert captured["open_telemetry"] is False

    custom_adapter = anthropic_adapter.AnthropicAdapter(
        model="claude-sonnet-5-5",
        api_key="test-key",
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_retries=0,
    )
    assert custom_adapter.max_retries == 0
    assert captured["max_retries"] == 0
