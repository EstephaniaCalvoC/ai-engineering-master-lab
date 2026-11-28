import asyncio
import importlib
import logging

import pytest

from app.config import get_service_settings
from app.context.estimation_system_prompt import ACTIVE_PROMPT_VERSION
from app.schemas.estimation import (
    DurationRange,
    EstimationOutputData,
    Phase,
    Task,
    TeamMember,
)
from app.services.llm import (
    LLMInvalidResponse,
    LLMRateLimited,
    LLMUnavailable,
)
from tests.helpers.llm import FakeAdapter, sample_estimate


def test_render_estimation_produces_text_estimate(estimation_service):
    text = estimation_service.render_estimation(sample_estimate())

    assert text == (
        "## Estimate\n"
        "### Task breakdown:\n"
        "**Design** (40 hours)\n"
        "1. UI/UX design: 40 hours\n"
        "\n"
        "**Development** (80 hours)\n"
        "2. Backend API: 60 hours\n"
        "3. Authentication: 20 hours\n"
        "\n"
        "**Total estimate: 120 hours**\n"
        "**Recommended team: 2 full-stack developer + 1 UX designer (part-time)**\n"
        "**Estimated duration: 6–8 weeks**\n"
    )


def test_render_estimation_handles_fractions_and_single_week(estimation_service):
    estimate = EstimationOutputData(
        phases=[Phase(name="Research", tasks=[Task(name="Spike", hours=17.5)])],
        team=[TeamMember(role="developer", count=1, part_time=False)],
        duration=DurationRange(min_weeks=2, max_weeks=2),
    )

    text = estimation_service.render_estimation(estimate)

    assert "1. Spike: 17.5 hours" in text
    assert "**Total estimate: 17.5 hours**" in text
    assert "**Estimated duration: 2 weeks**" in text


def test_generate_estimation_sends_prompt_to_adapter_and_returns_result(
    estimation_service, monkeypatch
):
    fake = FakeAdapter(reply=sample_estimate())
    monkeypatch.setattr(estimation_service, "llm", fake)
    monkeypatch.setattr(estimation_service, "fallback_llm", None)

    result = asyncio.run(estimation_service.generate_estimation("A" * 120))

    assert result == {
        "estimation": estimation_service.render_estimation(sample_estimate()),
        "estimation_output_data": sample_estimate(),
        "model": "fake-model",
        "provider": "fake",
        "system_prompt_version": ACTIVE_PROMPT_VERSION,
        "fallback_used": False,
    }
    assert len(fake.calls) == 1
    system_prompt, user_message, response_model = fake.calls[0]
    assert "Example #1" in system_prompt
    assert user_message == "A" * 120
    assert response_model is EstimationOutputData


def test_fallback_adapter_is_none_when_not_configured(estimation_service):
    assert estimation_service.fallback_llm is None


def test_fallback_adapter_is_built_when_configured(main_llm, monkeypatch):
    monkeypatch.setenv("FALLBACK_LLM_PROVIDER", "openai")
    monkeypatch.setenv("FALLBACK_LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("FALLBACK_PROVIDER_API_KEY", "TEST_FALLBACK_API_KEY")
    monkeypatch.setenv("TEST_FALLBACK_API_KEY", "sk-test-fallback")
    monkeypatch.setenv("LLM_MAX_RETRIES", "3")
    get_service_settings.cache_clear()

    import app.services.estimation as service

    importlib.reload(service)

    assert service.llm.max_retries == 3
    assert service.fallback_llm is not None
    assert service.fallback_llm.provider == "openai"
    assert service.fallback_llm.model == "gpt-4o"
    assert service.fallback_llm.max_retries == 3


@pytest.mark.parametrize(
    "provider_error",
    [
        LLMRateLimited("rate limited"),
        LLMUnavailable("provider down"),
    ],
)
def test_generate_estimation_falls_back_on_provider_errors(
    estimation_service, monkeypatch, caplog, provider_error
):
    main = FakeAdapter(provider="anthropic", model="claude-main", error=provider_error)
    fallback = FakeAdapter(
        reply=sample_estimate(), provider="openai", model="gpt-4o-fallback"
    )
    monkeypatch.setattr(estimation_service, "llm", main)
    monkeypatch.setattr(estimation_service, "fallback_llm", fallback)

    with caplog.at_level(logging.WARNING):
        result = asyncio.run(estimation_service.generate_estimation("A" * 120))

    assert result["provider"] == "openai"
    assert result["model"] == "gpt-4o-fallback"
    assert result["fallback_used"] is True
    assert result["estimation_output_data"] == sample_estimate()
    assert len(main.calls) == 1
    assert len(fallback.calls) == 1
    assert "falling back to openai/gpt-4o-fallback" in caplog.text


def test_generate_estimation_does_not_fall_back_on_invalid_response(
    estimation_service, monkeypatch
):
    main = FakeAdapter(error=LLMInvalidResponse("bad schema"))
    fallback = FakeAdapter(reply=sample_estimate(), provider="openai", model="gpt-4o")
    monkeypatch.setattr(estimation_service, "llm", main)
    monkeypatch.setattr(estimation_service, "fallback_llm", fallback)

    with pytest.raises(LLMInvalidResponse, match="bad schema"):
        asyncio.run(estimation_service.generate_estimation("A" * 120))

    assert len(main.calls) == 1
    assert len(fallback.calls) == 0


def test_generate_estimation_propagates_error_when_no_fallback_configured(
    estimation_service, monkeypatch
):
    main = FakeAdapter(error=LLMUnavailable("main down"))
    monkeypatch.setattr(estimation_service, "llm", main)
    monkeypatch.setattr(estimation_service, "fallback_llm", None)

    with pytest.raises(LLMUnavailable, match="main down"):
        asyncio.run(estimation_service.generate_estimation("A" * 120))


def test_generate_estimation_propagates_fallback_error_when_both_fail(
    estimation_service, monkeypatch
):
    main = FakeAdapter(error=LLMUnavailable("main down"))
    fallback = FakeAdapter(
        provider="openai", model="gpt-4o", error=LLMRateLimited("fallback limited")
    )
    monkeypatch.setattr(estimation_service, "llm", main)
    monkeypatch.setattr(estimation_service, "fallback_llm", fallback)

    with pytest.raises(LLMRateLimited, match="fallback limited"):
        asyncio.run(estimation_service.generate_estimation("A" * 120))

    assert len(main.calls) == 1
    assert len(fallback.calls) == 1
