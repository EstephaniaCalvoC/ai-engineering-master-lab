from types import SimpleNamespace

from pydantic import BaseModel

from app.schemas.estimation import (
    DurationRange,
    EstimationOutputData,
    Phase,
    Task,
    TeamMember,
)
from app.services.llm import LLMAdapter, LLMResult, anthropic_adapter, openai_adapter
from app.services.llm.anthropic_adapter import AnthropicAdapter
from app.services.llm.openai_adapter import OpenAIAdapter

# Output ceiling used in tests. Matches the MAX_OUTPUT_TOKENS default in app/config/service.py.
MAX_OUTPUT_TOKENS = 16_000


def sample_estimate() -> EstimationOutputData:
    """A valid estimate: 40 + 60 + 20 = 120 hours."""
    return EstimationOutputData(
        phases=[
            Phase(name="Design", tasks=[Task(name="UI/UX design", hours=40)]),
            Phase(
                name="Development",
                tasks=[
                    Task(name="Backend API", hours=60),
                    Task(name="Authentication", hours=20),
                ],
            ),
        ],
        team=[
            TeamMember(role="full-stack developer", count=2, part_time=False),
            TeamMember(role="UX designer", count=1, part_time=True),
        ],
        duration=DurationRange(min_weeks=6, max_weeks=8),
    )


class FakeAdapter(LLMAdapter):
    """Stands in for a real adapter in service tests. Records every call it receives."""

    provider = "fake"

    def __init__(
        self,
        reply: BaseModel | None = None,
        *,
        provider: str = "fake",
        model: str = "fake-model",
        error: Exception | None = None,
    ):
        super().__init__(model, MAX_OUTPUT_TOKENS)
        self.provider = provider
        self.reply = reply
        self.error = error
        self.calls: list[tuple[str, str, type[BaseModel]]] = []

    async def generate(self, system_prompt: str, user_message: str, response_model):
        self.calls.append((system_prompt, user_message, response_model))
        if self.error is not None:
            raise self.error
        return LLMResult(data=self.reply, model=self.model, provider=self.provider)


def make_anthropic_adapter(monkeypatch, parse, max_retries: int = 2):
    """Build a real AnthropicAdapter whose SDK client's messages.parse() is replaced by `parse`."""
    client = SimpleNamespace(messages=SimpleNamespace(parse=parse))
    monkeypatch.setattr(
        anthropic_adapter, "AsyncAnthropic", lambda api_key, **kwargs: client
    )
    return AnthropicAdapter(
        model="claude-sonnet-5-5",
        api_key="test-key",
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_retries=max_retries,
    )


def make_openai_adapter(monkeypatch, parse, max_retries: int = 2):
    """Build a real OpenAIAdapter whose SDK client's parse() is replaced by `parse`."""
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(parse=parse))
    )
    monkeypatch.setattr(openai_adapter, "AsyncOpenAI", lambda api_key, **kwargs: client)
    return OpenAIAdapter(
        model="gpt-4o",
        api_key="test-key",
        max_output_tokens=MAX_OUTPUT_TOKENS,
        max_retries=max_retries,
    )
