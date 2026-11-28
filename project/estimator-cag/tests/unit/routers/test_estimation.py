import pytest
from fastapi.testclient import TestClient

from app.config import get_service_settings
from app.services.llm import (
    LLMInvalidResponse,
    LLMRateLimited,
    LLMUnavailable,
)
from tests.helpers.llm import sample_estimate


def test_estimate_endpoint_returns_estimation_and_structured_estimate(
    main_llm, monkeypatch
):
    import app.routers.estimation as router_module

    async def fake_generate(transcription):
        return {
            "estimation": "## Estimate\n...",
            "estimation_output_data": sample_estimate(),
            "model": "m",
            "provider": "anthropic",
            "system_prompt_version": "test-version",
            "fallback_used": False,
        }

    monkeypatch.setattr(router_module, "generate_estimation", fake_generate)

    from app.main import app

    client = TestClient(app)
    response = client.post("/api/v1/estimate", json={"transcription": "A" * 120})

    assert response.status_code == 200
    body = response.json()
    assert body["estimation"] == "## Estimate\n..."
    assert body["model"] == "m"
    assert body["provider"] == "anthropic"
    assert body["system_prompt_version"] == "test-version"
    assert body["fallback_used"] is False
    assert body["estimation_output_data"]["total_hours"] == 120
    assert body["estimation_output_data"]["phases"][0] == {
        "name": "Design",
        "tasks": [{"name": "UI/UX design", "hours": 40.0}],
        "hours": 40.0,
    }
    assert body["estimation_output_data"]["duration"] == {
        "min_weeks": 6,
        "max_weeks": 8,
    }


def test_estimate_endpoint_rejects_oversized_transcription(main_llm, monkeypatch):
    monkeypatch.setenv("MAX_TRANSCRIPTION_LENGTH", "500")
    # Settings are cached on first use, so clear the cache after changing the limit
    get_service_settings.cache_clear()

    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/estimate",
        json={"transcription": "A" * 501},
    )

    assert response.status_code == 422


def test_estimate_endpoint_rejects_short_transcription(main_llm):
    from app.main import app

    client = TestClient(app)
    response = client.post("/api/v1/estimate", json={"transcription": "too short"})

    assert response.status_code == 422


def test_estimate_endpoint_rejects_empty_transcription(main_llm):
    from app.main import app

    client = TestClient(app)
    response = client.post("/api/v1/estimate", json={"transcription": ""})

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (LLMRateLimited("rate limited"), 429),
        (LLMUnavailable("provider down"), 503),
        (LLMInvalidResponse("bad schema"), 502),
    ],
)
def test_estimate_endpoint_maps_llm_errors_to_http_status(
    main_llm, monkeypatch, error, expected_status
):
    import app.routers.estimation as router_module

    async def failing_generate(transcription):
        raise error

    monkeypatch.setattr(router_module, "generate_estimation", failing_generate)

    from app.main import app

    client = TestClient(app)
    response = client.post("/api/v1/estimate", json={"transcription": "A" * 120})

    assert response.status_code == expected_status
    assert "detail" in response.json()
