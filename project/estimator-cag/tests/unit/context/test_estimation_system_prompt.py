import json

import pytest
from pydantic import ValidationError

from app.context import estimation_system_prompt as prompt_module
from app.context.estimation_system_prompt import (
    ACTIVE_PROMPT_VERSION,
    build_system_prompt,
    format_examples,
    load_system_prompt,
    render_system_prompt,
)
from app.schemas.estimation_system_prompt import (
    EstimationExampleJSON,
    EstimationExampleMarkdown,
    SystemPromptMarkdown,
)


@pytest.fixture
def prompt_files(tmp_path, monkeypatch):
    """Point the loader at a temporary folder of simplified prompt files."""
    monkeypatch.setattr(prompt_module, "PROMPTS_DIR", tmp_path)
    load_system_prompt.cache_clear()

    def write(version: str, data: dict) -> str:
        name = f"estimation_{version.replace('.', '_')}.json"
        (tmp_path / name).write_text(json.dumps(data), encoding="utf-8")
        return version

    yield write
    load_system_prompt.cache_clear()


def simple_prompt_data(render_format: str, examples: list[dict]) -> dict:
    return {
        "version": "9.9.1",
        "render_format": render_format,
        "template": "Intro\n{examples}\nOutro",
        "examples": examples,
    }


def make_prompt(**overrides) -> SystemPromptMarkdown:
    fields = {
        "version": "9.9.9",
        "render_format": "markdown",
        "template": "Intro\n{examples}\nOutro",
        "examples": [
            EstimationExampleMarkdown(
                meeting_summary="First project", estimation="10 hours"
            ),
            EstimationExampleMarkdown(
                meeting_summary="Second project", estimation="20 hours"
            ),
        ],
    }
    fields.update(overrides)
    return SystemPromptMarkdown(**fields)


def test_format_examples_numbers_each_example():
    text = format_examples(make_prompt().examples, "markdown")

    assert "Example #1\nMeeting Summary: First project\nEstimation:\n10 hours" in text
    assert "Example #2\nMeeting Summary: Second project\nEstimation:\n20 hours" in text


def test_build_system_prompt_inserts_examples_into_template():
    assert build_system_prompt(make_prompt()) == (
        "Intro\n"
        "Example #1\nMeeting Summary: First project\nEstimation:\n10 hours\n\n"
        "Example #2\nMeeting Summary: Second project\nEstimation:\n20 hours\n"
        "Outro"
    )


def test_build_system_prompt_pads_horizontal_rules_with_blank_lines():
    prompt = make_prompt(template="Intro paragraph.\n---\n{examples}\n---\nOutro")

    rendered = build_system_prompt(prompt)

    assert "Intro paragraph.\n\n---\n\nExample #1" in rendered
    assert "20 hours\n\n---\n\nOutro" in rendered


def test_active_prompt_file_loads_with_matching_version():
    prompt = load_system_prompt(ACTIVE_PROMPT_VERSION)

    assert prompt.version == ACTIVE_PROMPT_VERSION
    assert prompt.examples
    assert "{examples}" in prompt.template


def test_load_system_prompt_returns_cached_object(prompt_files):
    version = prompt_files(
        "9.9.1",
        simple_prompt_data("markdown", [{"meeting_summary": "a", "estimation": "b"}]),
    )
    first = load_system_prompt(version)

    assert load_system_prompt(version) is first


def test_loaded_prompt_is_frozen(prompt_files):
    version = prompt_files(
        "9.9.1",
        simple_prompt_data("markdown", [{"meeting_summary": "a", "estimation": "b"}]),
    )
    prompt = load_system_prompt(version)

    with pytest.raises(ValidationError):
        prompt.version = "2.0.0"
    assert isinstance(prompt.examples, tuple)


def test_json_prompt_file_renders_examples_as_compact_json(prompt_files):
    version = prompt_files(
        "9.9.1",
        simple_prompt_data(
            "json",
            [{"meeting_summary": {"client": "Acme"}, "estimation": {"total": 10}}],
        ),
    )

    text = build_system_prompt(load_system_prompt(version))

    assert text == (
        "Intro\n"
        "Example #1\n"
        'Meeting Summary:\n```json\n{"client":"Acme"}\n```\n'
        'Estimation:\n```json\n{"total":10}\n```\n'
        "Outro"
    )


def test_markdown_prompt_file_renders_text_examples_as_is(prompt_files):
    version = prompt_files(
        "9.9.1",
        simple_prompt_data(
            "markdown", [{"meeting_summary": "Acme app", "estimation": "10 hours"}]
        ),
    )

    text = build_system_prompt(load_system_prompt(version))

    assert text == (
        "Intro\nExample #1\nMeeting Summary: Acme app\nEstimation:\n10 hours\nOutro"
    )


def test_json_prompt_file_rejects_text_examples(prompt_files):
    version = prompt_files(
        "9.9.1",
        simple_prompt_data("json", [{"meeting_summary": "text", "estimation": "text"}]),
    )

    with pytest.raises(ValidationError):
        load_system_prompt(version)


def test_template_without_placeholder_is_rejected():
    with pytest.raises(ValidationError, match="placeholder"):
        make_prompt(template="No placeholder here")


@pytest.mark.parametrize("version", ["1.0", "v1.0.0", "1.0.0-beta"])
def test_version_must_be_semver(version):
    with pytest.raises(ValidationError):
        make_prompt(version=version)


def test_format_examples_renders_json_objects_as_compact_json():
    example = EstimationExampleJSON(
        meeting_summary={"client": "Acme"}, estimation={"phases": [], "total": 1}
    )

    text = format_examples([example], "json")

    assert 'Meeting Summary:\n```json\n{"client":"Acme"}\n```' in text
    assert 'Estimation:\n```json\n{"phases":[],"total":1}\n```' in text


def test_format_examples_renders_json_objects_as_markdown():
    example = EstimationExampleJSON(
        meeting_summary={"client": "Acme", "goals": ["speed", "cost"]},
        estimation={"phases": [{"name": "Build", "hours": 10}]},
    )

    text = format_examples([example], "markdown")

    assert (
        "Meeting Summary:\n- **client**: Acme\n- **goals**:\n  - speed\n  - cost"
        in text
    )
    assert "- **phases**:\n  -\n    - **name**: Build\n    - **hours**: 10" in text


def test_render_system_prompt_defaults_to_active_version():
    assert render_system_prompt() == build_system_prompt(
        load_system_prompt(ACTIVE_PROMPT_VERSION)
    )


def test_render_system_prompt_loads_requested_version(prompt_files):
    version = prompt_files(
        "9.9.1",
        simple_prompt_data("markdown", [{"meeting_summary": "a", "estimation": "b"}]),
    )

    assert render_system_prompt(version) == (
        "Intro\nExample #1\nMeeting Summary: a\nEstimation:\nb\nOutro"
    )


def test_render_format_must_be_known():
    with pytest.raises(ValidationError):
        make_prompt(render_format="yaml")
