# TODO

Scope: `estimator-cag/` (FastAPI service, Anthropic/OpenAI, CAG).

Items are sorted by priority, not by area. Priority reflects risk (cost, hangs, wrong results), what other items depend on, and what must exist before the service is exposed. Ticket IDs are stable and keep their area prefix: FDT = Foundations, CIC = CI/CD, SEC = Security and input limits, AID = AI design, FRT = Frontend, MON = Monitoring, TST = Testing, DOC = Documentation.

## P0: Do now (small, low-risk fixes for cost, hangs and bugs)

- FDT-001: [x] Add `ruff` (lint and format) to `estimator-cag/pyproject.toml` as a dev dependency, and fix the violations it reports.
- FDT-002: [x] Add a pytest marker for integration tests and skip them by default, so `uv run pytest` never calls a real LLM.
- SEC-001: [x] Add a maximum length to `transcription` in `app/schemas/estimation.py`. It only has `min_length=100` today, so one request can send an arbitrarily large prompt and cost.
- SEC-004: [x] Set an explicit timeout and `max_tokens` on the OpenAI call. The Anthropic call already has `max_tokens=4096`; the OpenAI call has neither.
- SEC-005: [x] Handle an empty `message.content` from the OpenAI response in `OpenAIAdapter.generate` (`app/services/llm/openai_adapter.py`). It currently returns `None`, which fails the response schema.

## P1: Next (core reliability; other items depend on these)

- AID-001: [x] Add an adapter layer for the LLM providers. Move `_build_client` and `_call_llm` out of `app/services/estimation.py` into `app/services/llm/`, with a common interface such as `generate(system_prompt, user_message) -> LLMResult`, one adapter per provider. Validate `MAIN_LLM_PROVIDER` against the supported values instead of accepting any string.
- AID-002: [x] Implement error handling. Define domain errors (`LLMUnavailable`, `LLMRateLimited`, `LLMInvalidResponse`) and map them to HTTP status codes in the router (502, 503, 429), instead of letting SDK exceptions surface as 500s.
- AID-003: [ ] Implement automatic retries for transient errors (429, 5xx, timeouts) with exponential backoff and jitter. Decide whether to use the SDK's `max_retries` or a wrapper, and log each retry.
- AID-004: [x] Implement fallback. `FALLBACK_LLM_PROVIDER`, `FALLBACK_LLM_MODEL` and `FALLBACK_PROVIDER_API_KEY` are already validated in `app/config/service.py` and documented in the README, but `generate_estimation` never uses them. Switch providers only on provider-level failures, not on invalid input, and record when the fallback was used.
- AID-007: [x] Request structured output (JSON with tasks, hours, team and duration) and validate it with a Pydantic model, instead of free text. Keep the current `estimation` text field for compatibility. Structured output makes evals and cost tracking possible.
- AID-005: [ ] Add prompt caching for the CAG context. The examples are sent in full on every request. Use Anthropic prompt caching (`cache_control` on the system block) and check the OpenAI caching behavior. Verify that the examples exceed the provider's minimum cacheable prompt length, or caching does nothing. Log cache read and write tokens.
- SEC-002: [ ] Add authentication to `/api/v1/estimate` (for example an API key header) before the container is exposed anywhere.
- MON-001: [ ] Add logs. `app/config/logger.py` already configures logging, so use it consistently in the router and service layers. Add a request ID to every request, and log provider, model, latency and status. Never log transcriptions or API keys, since transcriptions may contain client-confidential data.
- TST-002: [x] Cover the remaining gaps in unit tests: an empty transcription (422), and the error mapping once AID-002 exists. The OpenAI adapter, the unsupported-provider error, and the too-short transcription case are already covered in `tests/unit/`.
- TST-003: [ ] Add tests for retries, fallback selection, and cache-related request construction, using the fake LLM adapter.
- CIC-001: [ ] Create a GitHub Actions workflow that runs on PRs into `main`: `uv sync`, `uv run ruff check`, `uv run ruff format --check`, `uv run pytest`.

## P2: Planned (features and hardening)

- CIC-002: [ ] Create the server container: a `Dockerfile` (Python 3.11, uv, non-root user, `uvicorn app.main:app --host 0.0.0.0 --port 8001`) and a `.dockerignore` that excludes `.env`, `.venv`, `.pytest_cache` and `__pycache__`.
- SEC-003: [ ] Add rate limiting per client to protect the LLM budget.
- AID-010: [ ] Add guardrails. On input, reject transcriptions that are not project specs (off-topic text, prompt-injection attempts such as "ignore the system prompt"), and redact PII before the text reaches the provider. On output, validate the estimate against the structured schema and sanity bounds (hours above zero and below a ceiling, required sections present), and retry or return an error when it fails.
- AID-006: [x] Expand the examples in the prompt version files (`app/context/estimation_<version>.json`), adding a new version file for each change. There is one full example, and the second is a commented placeholder (`# ... second example`). Add several examples across project sizes, with consistent estimate formats.
- AID-009: [ ] Add evals to compare price and quality. Build a small golden set of transcriptions with expected ranges (hours within a tolerance, required sections present). Score each model and provider on quality and cost per request.
- AID-008: [x] Version the system prompt (a file with a version identifier) and return or log that version with each estimate.
- MON-003: [ ] Track token usage and estimated cost per request, and expose totals in logs or metrics.
- MON-002: [ ] Add LLM traces. Record a span for each LLM call with model, input and output tokens, latency, retry count and whether the fallback was used. Pick one backend (OpenTelemetry, Langfuse or similar) and document the choice.
- MON-005: [ ] Keep `/health` free of LLM calls. If a readiness check is needed, verify that settings load and the client is built, without spending tokens.
- TST-001: [x] Add integration tests that run the full path (router, service, real provider) behind the integration marker. Run them manually or in a scheduled job, since they cost money.
- FRT-003: [ ] Make the API base URL configurable through an environment variable. Add it to `.env.example` and the README table, as `estimator-cag/CLAUDE.md` requires for new variables.
- FRT-004: [ ] Add `streamlit` as a dependency, document the run command in the README (`uv run streamlit run frontend/app.py`), and include the frontend in ruff and CI.
- FRT-001: [ ] Add a basic Streamlit frontend at `estimator-cag/frontend/app.py`. It calls the API over HTTP rather than importing the service layer, and has a transcription text area with the 100-character minimum, an Estimate button, and a display of the result with provider and model.
- AID-011: [ ] Add chat mode. Let users refine an estimate through a multi-turn conversation: `POST /api/v1/estimation/chat` keeps the message history per conversation ID (in memory first, then a real store). Cap the history length or summarize older turns to stay within the context window, and keep the CAG examples cached across turns.
- FRT-002: [ ] Add a chat page to the Streamlit app once the chat endpoint exists.

## P3: Later (operations polish and monitoring)

- CIC-003: [ ] Build the image in CI after the checks pass, and push it to a registry on merge to the main branch.
- CIC-004: [ ] Add coverage reporting (`pytest-cov`) to CI, with a minimum threshold once the baseline is known.
- MON-004: [ ] Add LLM usage alerts and basic monitoring: error rate, p95 latency, fallback activation rate, and a daily spend threshold.
- DOC-001: [ ] Update the README API section with the error responses and status codes once they are implemented.
- DOC-002: [ ] Update the README tests section with the integration marker and how to run the integration tests.
- DOC-003: [ ] Document the fallback behavior and the retry policy in the README once they are implemented.
