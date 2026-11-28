import pytest
from pydantic import ValidationError

from app.schemas.estimation import DurationRange, EstimationOutputData, Phase, Task
from tests.helpers.llm import sample_estimate


def test_total_hours_is_sum_of_tasks():
    assert sample_estimate().total_hours == 120


def test_total_hours_is_in_serialized_output_but_not_in_llm_schema():
    estimate = sample_estimate()

    assert estimate.model_dump()["total_hours"] == 120
    # The model sees the schema for validation, so it is not asked to compute the total
    assert "total_hours" not in EstimationOutputData.model_json_schema()["properties"]


@pytest.mark.parametrize("hours", [0, -5])
def test_task_hours_must_be_positive(hours):
    with pytest.raises(ValidationError):
        Task(name="Backend", hours=hours)


def test_phase_hours_is_sum_of_its_tasks():
    assert sample_estimate().phases[1].hours == 80


def test_phase_needs_at_least_one_task():
    with pytest.raises(ValidationError):
        Phase(name="Empty", tasks=[])


def test_estimate_needs_at_least_one_phase():
    with pytest.raises(ValidationError):
        EstimationOutputData(
            phases=[],
            team=sample_estimate().team,
            duration=DurationRange(min_weeks=1, max_weeks=2),
        )


def test_duration_min_must_not_exceed_max():
    with pytest.raises(ValidationError, match="min_weeks must not be greater"):
        DurationRange(min_weeks=8, max_weeks=6)
