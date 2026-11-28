"""Full path with Anthropic: router, service and provider (TST-001).

Calls the real provider and costs money. Run by hand with:

    uv run --env-file tests/integration/.env.integration pytest tests/integration/test_estimate_endpoint_anthropic.py --run-integration

tests/integration/.env.integration only needs the provider API keys (secrets). Each test
configures its service settings through the `make_client` fixture in
tests/integration/conftest.py, which sets the env vars and reloads the service module.
"""

from app.schemas.estimation import EstimationResponse


def test_estimate_returns_structured_estimate_from_anthropic(
    make_client, sample_transcript
):
    client = make_client(
        MAIN_LLM_PROVIDER="anthropic",
        MAIN_LLM_MODEL="claude-haiku-4-5",
        MAIN_PROVIDER_API_KEY="ANTHROPIC_API_KEY",
    )

    response = client.post(
        "/api/v1/estimate", json={"transcription": sample_transcript}
    )

    assert response.status_code == 200, response.text
    body = EstimationResponse.model_validate(response.json())
    assert body.provider == "anthropic"
    assert body.model == "claude-haiku-4-5"
    assert body.system_prompt_version

    assert body.estimation.startswith("## Estimate")
    print(body.estimation)

    estimate = body.estimation_output_data
    assert estimate.phases
    assert estimate.team
    assert estimate.total_hours > 0
