from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

ModelT = TypeVar("ModelT", bound=BaseModel)

# Default number of SDK retries on transient provider errors (429, 5xx, timeouts).
DEFAULT_MAX_RETRIES = 2


class LLMResult(BaseModel, Generic[ModelT]):
    # Immutable, so nothing downstream can change the reply after the adapter returns it.
    model_config = ConfigDict(frozen=True)

    # The reply, already validated against the response model the caller asked for
    data: ModelT
    model: str
    provider: str


class LLMAdapter(ABC):
    """Common interface for LLM providers. Each provider has one adapter that hides its SDK."""

    # Name used in settings (MAIN_LLM_PROVIDER) and in results. Set by each subclass.
    provider: str

    def __init__(
        self,
        model: str,
        max_output_tokens: int,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.model = model
        # Output ceiling per reply, from settings (MAX_OUTPUT_TOKENS)
        self.max_output_tokens = max_output_tokens
        # Transient-error retry ceiling passed to the provider SDK (LLM_MAX_RETRIES)
        self.max_retries = max_retries

    @abstractmethod
    async def generate(
        self, system_prompt: str, user_message: str, response_model: type[ModelT]
    ) -> LLMResult[ModelT]:
        """Send one system prompt and one user message, and return a reply that matches
        response_model. Raises LLMRateLimited, LLMUnavailable, or LLMInvalidResponse
        when the provider call fails or returns an unusable reply."""
