import pytest
from pydantic import ValidationError

from app.services.llm import LLMResult
from tests.helpers.llm import sample_estimate


def test_llm_result_is_immutable():
    result = LLMResult(data=sample_estimate(), model="m", provider="anthropic")

    with pytest.raises(ValidationError):
        result.model = "changed"
