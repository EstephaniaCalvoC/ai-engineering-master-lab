import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas.estimation_system_prompt import (
    EstimationExampleJSON,
    EstimationExampleMarkdown,
    SystemPrompt,
    SystemPromptJSON,
    SystemPromptMarkdown,
)

JSON_EXAMPLE = {"meeting_summary": {"client": "Acme"}, "estimation": {"total": 10}}
MARKDOWN_EXAMPLE = {"meeting_summary": "Summary", "estimation": "10 hours"}

prompt_adapter = TypeAdapter(SystemPrompt)


def prompt_data(render_format: str, examples: list[dict]) -> dict:
    return {
        "version": "1.0.0",
        "render_format": render_format,
        "template": "Intro\n{examples}",
        "examples": examples,
    }


def test_json_example_accepts_objects():
    example = EstimationExampleJSON(**JSON_EXAMPLE)

    assert example.meeting_summary == {"client": "Acme"}
    assert example.estimation == {"total": 10}


def test_json_example_rejects_text():
    with pytest.raises(ValidationError):
        EstimationExampleJSON(**MARKDOWN_EXAMPLE)


def test_markdown_example_accepts_text():
    example = EstimationExampleMarkdown(**MARKDOWN_EXAMPLE)

    assert example.meeting_summary == "Summary"
    assert example.estimation == "10 hours"


def test_markdown_example_rejects_objects():
    with pytest.raises(ValidationError):
        EstimationExampleMarkdown(**JSON_EXAMPLE)


def test_json_render_format_selects_json_prompt():
    prompt = prompt_adapter.validate_python(prompt_data("json", [JSON_EXAMPLE]))

    assert isinstance(prompt, SystemPromptJSON)
    assert isinstance(prompt.examples[0], EstimationExampleJSON)


def test_markdown_render_format_selects_markdown_prompt():
    prompt = prompt_adapter.validate_python(prompt_data("markdown", [MARKDOWN_EXAMPLE]))

    assert isinstance(prompt, SystemPromptMarkdown)
    assert isinstance(prompt.examples[0], EstimationExampleMarkdown)


def test_json_render_format_rejects_markdown_examples():
    with pytest.raises(ValidationError):
        SystemPromptJSON(**prompt_data("json", [MARKDOWN_EXAMPLE]))


def test_markdown_render_format_rejects_json_examples():
    with pytest.raises(ValidationError):
        SystemPromptMarkdown(**prompt_data("markdown", [JSON_EXAMPLE]))


def test_already_built_example_of_wrong_class_is_rejected():
    with pytest.raises(ValidationError):
        SystemPromptMarkdown(
            **prompt_data("markdown", [EstimationExampleJSON(**JSON_EXAMPLE)])
        )


def test_unknown_render_format_is_rejected():
    with pytest.raises(ValidationError):
        prompt_adapter.validate_python(prompt_data("yaml", [MARKDOWN_EXAMPLE]))


def test_examples_are_stored_as_tuple():
    prompt = prompt_adapter.validate_python(prompt_data("markdown", [MARKDOWN_EXAMPLE]))

    assert isinstance(prompt.examples, tuple)
