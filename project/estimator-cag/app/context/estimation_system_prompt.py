import argparse
import json
import re
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from app.schemas.estimation_system_prompt import (
    EstimationExampleJSON,
    EstimationExampleMarkdown,
    SystemPrompt,
)

PROMPTS_DIR = Path(__file__).parent

# Validates the discriminated union, so render_format picks the example class
_system_prompt_adapter: TypeAdapter[SystemPrompt] = TypeAdapter(SystemPrompt)

# Version used for live estimates. Evals can load any other version with load_system_prompt().
ACTIVE_PROMPT_VERSION = "1.2.0"


# Cached: each version file is read once per process, up to 16 versions. The result is frozen,
# so callers share it safely.
@lru_cache(maxsize=16)
def load_system_prompt(version: str) -> SystemPrompt:
    """Read app/context/estimation_<version>.json, e.g. 1.0.0 -> estimation_1_0_0.json."""
    path = PROMPTS_DIR / f"estimation_{version.replace('.', '_')}.json"
    return _system_prompt_adapter.validate_json(path.read_text(encoding="utf-8"))


def to_markdown(value: Any, depth: int = 0) -> str:
    """Render a JSON value as a nested markdown bullet list."""
    pad = "  " * depth
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if isinstance(item, dict | list):
                lines.append(f"{pad}- **{key}**:\n{to_markdown(item, depth + 1)}")
            else:
                lines.append(f"{pad}- **{key}**: {item}")
        return "\n".join(lines)
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict | list):
                lines.append(f"{pad}-\n{to_markdown(item, depth + 1)}")
            else:
                lines.append(f"{pad}- {item}")
        return "\n".join(lines)
    return f"{pad}{value}"


# A standalone "---" immediately after a non-blank line is parsed by Markdown as a
# Setext <h2> heading underline instead of a horizontal rule. These patterns ensure
# blank lines around standalone "---" dividers across all prompt versions.
_HORIZONTAL_RULE_BEFORE_RE = re.compile(r"(?m)(?<!\n)\n(---)$")
_HORIZONTAL_RULE_AFTER_RE = re.compile(r"(?m)^(---)\n(?!\n)")


def _normalize_horizontal_rules(text: str) -> str:
    text = _HORIZONTAL_RULE_BEFORE_RE.sub(r"\n\n\1", text)
    return _HORIZONTAL_RULE_AFTER_RE.sub(r"\1\n\n", text)


def render_value(value: str | dict[str, Any], render_format: str) -> str:
    """Return text as is, and render a JSON object as a fenced JSON block or as markdown."""
    if isinstance(value, str):
        return value
    if render_format == "json":
        # Compact on purpose: the output is forced into a schema, so the examples only
        # need to show content, and whitespace would cost tokens without helping.
        # Wrapped in a fenced code block so Markdown renderers do not interpret
        # characters inside the JSON (e.g. "~" as strikethrough).
        compact = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        return f"```json\n{compact}\n```"
    return to_markdown(value)


def format_examples(
    examples: Sequence[EstimationExampleJSON | EstimationExampleMarkdown],
    render_format: str,
) -> str:
    parts = []
    for n, example in enumerate(examples, start=1):
        summary = render_value(example.meeting_summary, render_format)
        estimation = render_value(example.estimation, render_format)
        # Fenced code blocks and markdown lists must start on their own line to render validly.
        summary_sep = "\n" if summary.startswith(("```", "- ")) else " "
        parts.append(
            f"Example #{n}\n"
            f"Meeting Summary:{summary_sep}{summary}\n"
            f"Estimation:\n{estimation}"
        )
    return "\n\n".join(parts)


def build_system_prompt(prompt: SystemPrompt) -> str:
    rendered = prompt.template.format(
        examples=format_examples(prompt.examples, prompt.render_format)
    )
    return _normalize_horizontal_rules(rendered)


def render_system_prompt(version: str = ACTIVE_PROMPT_VERSION) -> str:
    """Load and render the system prompt for a version (defaults to the active version)."""
    return build_system_prompt(load_system_prompt(version))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render a versioned estimation system prompt to inspect its output."
    )
    parser.add_argument(
        "version",
        nargs="?",
        default=ACTIVE_PROMPT_VERSION,
        help=f"Prompt version to render (default: {ACTIVE_PROMPT_VERSION}).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional file path to write the rendered prompt (e.g. prompt.md).",
    )
    args = parser.parse_args()
    output_text = render_system_prompt(args.version)
    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
    else:
        print(output_text)
