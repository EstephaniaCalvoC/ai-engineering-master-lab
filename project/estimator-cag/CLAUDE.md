# Estimator CAG

FastAPI service (Python 3.11, managed with uv) that estimates the cost and time of a software project from a spec transcription. Uses a layered architecture and CAG. See README.md for architecture, endpoints, and env vars.

## Commands

- Install dependencies: `uv sync`
- Run the server: `uv run uvicorn app.main:app --reload --port 8001`
- Run tests: `uv run pytest`
- Run integration tests (real LLM calls, cost money; run by hand only): `uv run --env-file tests/integration/.env.integration pytest tests/integration --run-integration`
- Lint: `uv run ruff check` (add `--fix` to apply safe fixes)
- Format: `uv run ruff format` (check only, without writing: `uv run ruff format --check`)
- Add a dependency: `uv add <package>` (dev only: `uv add --dev <package>`)
- Before finishing a change, run `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest`. All three must pass.

## Secrets

- Never read, print, edit, or source `.env` or `tests/integration/.env.integration`. Both hold real API keys. Read `.env.example` for variable names.
- Access secrets only through environment variables in code, never by hardcoding them.
- A `PreToolUse` hook (`.claude/hooks/block_secrets.py`, configured in `.claude/settings.json`) blocks Claude's tool calls that read or edit `.env` or `tests/integration/.env.integration`, and blocks any command with `--run-integration`. Only the user runs integration tests, from their own terminal.
- Tests must not call real LLM APIs. Mock the LLM client. The only exception is `tests/integration/`, which runs only with `--run-integration`, reads API keys from `tests/integration/.env.integration` through `uv run --env-file`, and configures per-test service settings via `make_client` in `tests/integration/conftest.py`.

## Conventions

- Keep routers in `app/routers/` thin: HTTP handling only. Put logic and LLM calls in `app/services/`, and request/response models in `app/schemas/`.
- Test routers with FastAPI's `TestClient`, and test services directly with a mocked LLM.
- Test fixtures: `tests/conftest.py` only registers the `--run-integration` flag and the skip logic. `tests/unit/conftest.py` provides `isolated_env` (temp directory, cleared settings and key variables) and `main_llm`. `tests/integration/conftest.py` provides `isolated_integration_env` (temp directory, cleared settings variables while keeping API keys from `.env.integration`) and `make_client(**env_overrides)` (applies per-test settings and reloads `app.services.estimation`).
- Read configuration through `app/config/`. Any new env var goes in `.env.example` and the README table.
- Write code, comments, and docs in English.

## Backlog

- The backlog is `../backlog.md` at the repo root. Items are sorted by priority (P0 to P3) and have ticket IDs such as `AID-003`. Check the ticket and its tier before starting work on it.
- When a ticket is done, change its `[ ]` to `[x]`. Keep ticket IDs unchanged, and give new tickets the next free number in their area.
- Reference the ticket ID in commit messages and pull request descriptions.
