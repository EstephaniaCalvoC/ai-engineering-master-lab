# schemas/estimation.py
from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from app.config import get_service_settings


class EstimationRequest(BaseModel):
    transcription: str = Field(description="Client's meeting transcription")

    @field_validator("transcription", mode="after")
    @classmethod
    def check_length(cls, value: str) -> str:
        # Bounds come from settings so they can be tuned per deployment
        settings = get_service_settings()
        if not (
            settings.MIN_TRANSCRIPTION_LENGTH
            <= len(value)
            <= settings.MAX_TRANSCRIPTION_LENGTH
        ):
            raise ValueError(
                f"must be between {settings.MIN_TRANSCRIPTION_LENGTH} and "
                f"{settings.MAX_TRANSCRIPTION_LENGTH} characters"
            )
        return value


class Task(BaseModel):
    name: str = Field(min_length=1, description="Short name of the work item")
    hours: float = Field(gt=0, description="Estimated effort for this task, in hours")


class Phase(BaseModel):
    name: str = Field(min_length=1, description="Phase name, such as 'Backend'")
    tasks: list[Task] = Field(min_length=1, description="Tasks of this phase")

    @computed_field
    @property
    def hours(self) -> float:
        return sum(task.hours for task in self.tasks)


class TeamMember(BaseModel):
    role: str = Field(min_length=1, description="Role, such as 'full-stack developer'")
    count: int = Field(ge=1, description="Number of people in this role")
    part_time: bool = Field(description="True if this role works part-time")


class DurationRange(BaseModel):
    min_weeks: int = Field(ge=1, description="Shortest expected duration, in weeks")
    max_weeks: int = Field(ge=1, description="Longest expected duration, in weeks")

    @model_validator(mode="after")
    def check_order(self):
        if self.min_weeks > self.max_weeks:
            raise ValueError("min_weeks must not be greater than max_weeks")
        return self


class EstimationOutputData(BaseModel):
    """Structured estimate. The LLM fills the fields; the totals are computed from the tasks."""

    phases: list[Phase] = Field(
        min_length=1, description="Work breakdown, grouped by phase"
    )
    team: list[TeamMember] = Field(min_length=1, description="Recommended team")
    duration: DurationRange = Field(description="Expected calendar duration")

    @computed_field
    @property
    def total_hours(self) -> float:
        # Summed in code rather than by the model, so the total is always consistent
        return sum(phase.hours for phase in self.phases)


class EstimationResponse(BaseModel):
    # Plain-text estimate, kept for compatibility with existing clients
    estimation: str
    # The same estimate as structured data
    estimation_output_data: EstimationOutputData
    model: str
    provider: str
    # Version of the system prompt that produced this estimate (app/context/estimation_system_prompt.py)
    system_prompt_version: str
    # True when the main provider failed and the fallback provider produced this estimate
    fallback_used: bool = False
