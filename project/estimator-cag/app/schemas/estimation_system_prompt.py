from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EstimationExampleJSON(BaseModel):
    """Example whose summary and estimate are JSON objects, for render_format "json"."""

    meeting_summary: dict[str, Any] = Field(description="Summary of a past project")
    estimation: dict[str, Any] = Field(
        description="Reference estimate for that project"
    )


class EstimationExampleMarkdown(BaseModel):
    """Example whose summary and estimate are already written as text, used as is."""

    meeting_summary: str = Field(description="Summary of a past project")
    estimation: str = Field(description="Reference estimate for that project")


class SystemPromptBase(BaseModel):
    """Fields shared by every versioned system prompt."""

    model_config = ConfigDict(frozen=True)

    version: str = Field(
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version, such as 1.0.0. The file name is derived from it.",
    )
    template: str = Field(description="Prompt text with an {examples} placeholder")

    @field_validator("template")
    @classmethod
    def check_placeholder(cls, value: str) -> str:
        if "{examples}" not in value:
            raise ValueError("template must contain the {examples} placeholder")
        return value


class SystemPromptJSON(SystemPromptBase):
    """System prompt whose examples are JSON objects rendered as JSON text."""

    render_format: Literal["json"] = Field(
        description="Examples are rendered as indented JSON text."
    )
    # A tuple rather than a list, so the cached prompt cannot be changed in place
    examples: tuple[EstimationExampleJSON, ...] = Field(
        description="Historical estimates, inserted into the template in order"
    )


class SystemPromptMarkdown(SystemPromptBase):
    """System prompt whose examples are already text, used as is."""

    render_format: Literal["markdown"] = Field(
        description="Examples are already written as markdown text."
    )
    # A tuple rather than a list, so the cached prompt cannot be changed in place
    examples: tuple[EstimationExampleMarkdown, ...] = Field(
        description="Historical estimates, inserted into the template in order"
    )


# The render_format field picks the class, so each prompt file is validated against its own example type
SystemPrompt = Annotated[
    SystemPromptJSON | SystemPromptMarkdown,
    Field(discriminator="render_format"),
]
