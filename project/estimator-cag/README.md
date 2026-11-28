# Estimator CAG

Exercise for the second session of the AI Engineer Master at LIDR.

This project shows how to structure an **AI Software Development Estimator** using a layered architecture and **CAG (Cache-Augmented Generation)**.

## What it does

The estimator helps dev teams estimate the cost and time of a software development project from a transcription of the project specs.

Basic flow:

1. The client calls the `/api/v1/estimate` endpoint with the transcription.
2. The router passes the request to the service layer, which calls an LLM with instructions to produce the estimation.
3. The versioned system prompt in `app/context/` is loaded at startup. It includes the historical estimates (the examples) that are preloaded into the prompt. This is the CAG part: the context is cached and reused instead of being retrieved per request.
4. The LLM creates the estimation.
5. A service function processes and formats the LLM response.
6. The server responds with the formatted estimation.

## Architecture

The code is split into layers, each with one responsibility:

| Layer | Folder | Responsibility |
|-------|--------|----------------|
| Transport | `app/routers/` | HTTP endpoints. Receives requests and returns responses. |
| Business logic | `app/services/` | Prompt building and response processing. |
| LLM adapters | `app/services/llm/` | One adapter per provider behind a common `generate()` interface. Each adapter wraps its provider's SDK. |
| Data contracts | `app/schemas/` | Request and response models. |
| Reference data | `app/context/` | Versioned system prompts (`estimation_<version>.json`), each with its own examples, loaded into the prompt for CAG. |

`app/config/` holds the centralized setup. `server.py` has `ServerSettings` (`APP_ENV`, `LOG_LEVEL`, `HOST`, `PORT`) and `service.py` has `ServiceSettings` (LLM provider, model, and API key settings). Use `get_server_settings()` and `get_service_settings()` to read them. `logger.py` configures logging from `LOG_LEVEL`. `app/main.py` is the entry point that creates the FastAPI app.

The LLM service supports `anthropic` and `openai` as the main provider. It selects the provider from `MAIN_LLM_PROVIDER`, and settings reject any other value at startup. Each provider has an adapter in `app/services/llm/` that implements `generate(system_prompt, user_message, response_model)` and returns an `LLMResult` whose `data` is an instance of `response_model`, so the service code does not depend on a specific SDK. The adapters ask the provider for structured output: Anthropic through `messages.parse` (sent as `output_config.format`, a JSON schema), OpenAI through `chat.completions.parse`. The reply is validated against the Pydantic model in `app/schemas/estimation.py` (`EstimationOutputData`: phases with tasks and hours, team, and duration in weeks). The plain-text `estimation` field is rendered from that structured estimate.

### File structure

```
estimator-cag/
├── app/
│   ├── __init__.py
│   ├── main.py               ← App entry point
│   ├── config/               ← Centralized setup
│   │   ├── __init__.py
│   │   ├── env.py            ← .env path and env var lookup
│   │   ├── server.py         ← ServerSettings
│   │   ├── service.py        ← ServiceSettings
│   │   ├── tracing.py        ← TracingSettings and Arize AX OpenTelemetry setup
│   │   └── logger.py         ← Logging setup
│   │
│   ├── routers/              ← HTTP endpoints (transport layer)
│   │   ├── __init__.py
│   │   └── estimation.py     ← POST /api/v1/estimate
│   │
│   ├── context/              ← Versioned system prompts for CAG (reference data)
│   │   ├── __init__.py
│   │   ├── estimation_system_prompt.py  ← ACTIVE_PROMPT_VERSION, cached load and build functions
│   │   ├── estimation_<version>.json ← One file per version: template and examples
│   │   └── estimation_system_prompt_log.md ← Version history of the system prompt
│   │
│   ├── services/             ← Business logic (intelligence layer)
│   │   ├── __init__.py
│   │   ├── estimation.py     ← Prompt building and LLM calls
│   │   └── llm/              ← Provider adapters behind one generate() interface
│   │       ├── __init__.py
│   │       ├── base.py       ← LLMAdapter and LLMResult
│   │       ├── factory.py    ← Builds the adapter for a provider name
│   │       ├── anthropic_adapter.py
│   │       └── openai_adapter.py
│   │
│   └── schemas/              ← Data contracts (request/response)
│       ├── __init__.py
│       ├── estimation.py
│       └── estimation_system_prompt.py  ← SystemPrompt (JSON or markdown examples) and the example models
│
├── postman/                  ← Postman collection for manual calls
│   └── estimate.postman_collection.json
├── tests/
│   ├── conftest.py           ← Shared fixtures (isolated env, main_llm) and the integration opt-in
│   ├── helpers/              ← Shared fakes and adapter factories
│   ├── unit/                 ← Tests with mocked LLMs (run by default), mirrors app/
│   │   ├── config/
│   │   ├── context/
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── services/
│   │       └── llm/
│   └── integration/          ← Tests that call real LLMs (opt-in)
├── .env                      ← Local secrets (git-ignored)
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
└── uv.lock
```

## Setup

Requirements:

- Python 3.11 (see `.python-version`)
- [uv](https://docs.astral.sh/uv/)

```bash
# 1. Create your local env file and add your API key(s)
cp .env.example .env

# 2. Install dependencies
uv sync

# 3. Start the dev server
uv run uvicorn app.main:app --reload --port 8001
```

The server runs at `http://127.0.0.1:8001`. Open `http://127.0.0.1:8001/docs` for the interactive API documentation.

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `APP_ENV` | No | Runtime environment, such as `development` or `production`. Defaults to `development`. |
| `LOG_LEVEL` | No | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. Defaults to `DEBUG`. |
| `MAIN_LLM_PROVIDER` | Yes | Main LLM provider to use: `anthropic` or `openai`. |
| `MAIN_LLM_MODEL` | Yes | Main model ID for the selected provider, such as `claude-sonnet-5-5` for Anthropic. |
| `MAIN_PROVIDER_API_KEY` | Yes | Name of the environment variable that holds the main provider's API key, such as `ANTHROPIC_API_KEY`. This is the name, not the key. |
| `FALLBACK_LLM_PROVIDER` | No | Fallback LLM provider, used if the main provider fails: `anthropic` or `openai`. Leave empty to disable the fallback. |
| `FALLBACK_LLM_MODEL` | If `FALLBACK_LLM_PROVIDER` is set | Model ID for the fallback provider, such as `gpt-4o` for OpenAI. |
| `FALLBACK_PROVIDER_API_KEY` | If `FALLBACK_LLM_PROVIDER` is set | Name of the environment variable that holds the fallback provider's API key, such as `OPENAI_API_KEY`. This is the name, not the key. |
| `ANTHROPIC_API_KEY` | Only if referenced | API key value for Anthropic models. The app reads it through the name in `MAIN_PROVIDER_API_KEY` or `FALLBACK_PROVIDER_API_KEY`. |
| `OPENAI_API_KEY` | Only if referenced | API key value for OpenAI models. The app reads it through the name in `MAIN_PROVIDER_API_KEY` or `FALLBACK_PROVIDER_API_KEY`. |
| `MIN_TRANSCRIPTION_LENGTH` | No | Minimum transcription length in characters. Defaults to `100`. Must not be greater than `MAX_TRANSCRIPTION_LENGTH`. |
| `MAX_TRANSCRIPTION_LENGTH` | No | Maximum transcription length in characters. Limits prompt size and cost. Defaults to `20000`. |
| `MAX_OUTPUT_TOKENS` | No | Maximum output tokens per LLM reply. Must not be greater than `16000`, since some OpenAI models reject larger values. Defaults to `16000`. |
| `LLM_MAX_RETRIES` | No | Number of automatic retries performed by the provider SDK on transient errors (429, 5xx, timeouts). Defaults to `2`. Set to `0` to disable retries. |
| `HOST` | No | Server host. Defaults to `127.0.0.1`. |
| `PORT` | No | Server port. Defaults to `8001`. |
| `TRACING_ENABLED` | No | Enable or disable Arize AX tracing. Defaults to `true`. Tracing is skipped if `ARIZE_SPACE_ID` or `ARIZE_API_KEY` is unset. |
| `ARIZE_SPACE_ID` | Only for tracing | Base64 Arize Space ID for trace export (not the space name). |
| `ARIZE_API_KEY` | Only for tracing | Arize API key for trace export. Never commit `.env`. |
| `ARIZE_PROJECT_NAME` | No | Project name in Arize AX. Defaults to `estimator-cag`. |
| `ARIZE_COLLECTOR_ENDPOINT` | No | Arize OTLP gRPC collector endpoint. Defaults to US (`https://otlp.arize.com/v1`). |

Each provider's API key lives in its own variable. `MAIN_PROVIDER_API_KEY` and `FALLBACK_PROVIDER_API_KEY` hold the name of that variable, so you can change providers without changing code. Never commit `.env`.

### Arize AX CLI (`ax`)

If you use the Arize AX CLI (`arize-ax-cli`) alongside the Arize agent skills, install it with `arize` pinned below `8.65.0`:

```bash
uv tool install arize-ax-cli --python 3.11 --with "arize<8.65.0" --force
```

`arize-ax-cli==0.39.0` references `Region.US_EAST_1B` at import time, which was removed in `arize==8.65.0` and causes `ax` to fail with `RuntimeError: Failed to load command module 'ax.commands.ai_integrations': US_EAST_1B`. Pinning `arize<8.65.0` resolves `arize==8.64.0` and avoids the error until a compatible `arize-ax-cli` release is published.

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/estimate` | Takes the project transcription (`transcription`, within `MIN_TRANSCRIPTION_LENGTH` and `MAX_TRANSCRIPTION_LENGTH`, by default 100 to 20,000 characters) and returns the estimation as text (`estimation`), the same estimate as structured data (`estimation_output_data`: `phases` with their `tasks` and `hours`, `total_hours`, `team`, `duration`), the provider and model used, the system prompt version (`system_prompt_version`) that produced it, and `fallback_used` (`true` when the main provider failed with a rate-limit or availability error and the fallback provider handled the request). |
| `GET` | `/health` | Health check. Returns `200 OK` with `{"status": "healthy"}` when the server is running. |

Example request:

```bash
curl -X POST http://127.0.0.1:8001/api/v1/estimate \
  -H 'Content-Type: application/json' \
  -d '{"transcription": "<at least 100 characters describing the project>"}'
```

## Debugging and manual testing

- **VS Code debugger:** the launch configuration `Estimator: debug /estimate` is in the repository's `.vscode/launch.json`. Open the Run and Debug panel, pick that configuration, and press F5. It runs uvicorn on port 8001 with the project's `.venv`, without `--reload`, so breakpoints stay attached.
- **Postman:** import `postman/estimate.postman_collection.json` into Postman. It contains one request, `Estimate project`, which posts a sample transcription to `{{base_url}}/api/v1/estimate`. Change `base_url` to `http://127.0.0.1:8001` if `localhost` doesn't connect.

## Tests

Run the tests with `uv run pytest`. They live in two folders:

- `tests/unit/` runs by default and never calls real LLM APIs. The service tests use a fake adapter, the adapter tests replace each provider's SDK client, and the router tests use FastAPI's `TestClient`.
- `tests/integration/` calls real LLM APIs and costs money. Its tests are skipped unless you pass `--run-integration`, for example `uv run pytest tests/integration --run-integration`.

## Backlog

Planned work is tracked in [`../backlog.md`](../backlog.md). Items are sorted by priority: P0 (do now), P1 (next), P2 (planned), and P3 (later). Each item has a ticket ID with an area prefix:

| Prefix | Area |
|--------|------|
| `FDT` | Foundations |
| `CIC` | CI/CD |
| `SEC` | Security and input limits |
| `AID` | AI design |
| `FRT` | Frontend |
| `MON` | Monitoring |
| `TST` | Testing |
| `DOC` | Documentation |

Reference the ticket ID in commit messages and pull request descriptions, for example `AID-003: add retries with backoff`.
