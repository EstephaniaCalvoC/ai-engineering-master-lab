import anthropic
from anthropic import AsyncAnthropic
from pydantic import ValidationError

from app.services.llm.base import DEFAULT_MAX_RETRIES, LLMAdapter, LLMResult, ModelT
from app.services.llm.errors import (
    LLMInvalidResponse,
    LLMRateLimited,
    LLMUnavailable,
)


class AnthropicAdapter(LLMAdapter):
    provider = "anthropic"

    def __init__(
        self,
        model: str,
        api_key: str,
        max_output_tokens: int,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        super().__init__(model, max_output_tokens, max_retries)
        # Disable the SDK's built-in OpenTelemetry spans so OpenInference does not emit duplicates
        self._client = AsyncAnthropic(
            api_key=api_key, open_telemetry=False, max_retries=max_retries
        )

    async def generate(
        self, system_prompt: str, user_message: str, response_model: type[ModelT]
    ) -> LLMResult[ModelT]:
        # parse() sends response_model as output_config.format (a JSON schema), so the reply
        # is JSON that matches the model. The SDK moves constraints the API does not support
        # (such as minimum and minLength) into the schema descriptions, and the reply is then
        # validated against response_model here.
        try:
            response = await self._client.messages.parse(
                model=self.model,
                max_tokens=self.max_output_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                output_format=response_model,
            )
        except anthropic.RateLimitError as exc:
            raise LLMRateLimited(f"Anthropic rate limit exceeded: {exc}") from exc
        except anthropic.APIResponseValidationError as exc:
            raise LLMInvalidResponse(
                f"Anthropic returned an invalid API response: {exc}"
            ) from exc
        except anthropic.AnthropicError as exc:
            raise LLMUnavailable(f"Anthropic API error: {exc}") from exc
        except ValidationError as exc:
            raise LLMInvalidResponse(
                f"Anthropic reply did not match expected schema: {exc}"
            ) from exc

        # A reply cut off by max_tokens would be incomplete JSON; say so instead of a generic error
        if response.stop_reason == "max_tokens":
            raise LLMInvalidResponse(
                "Anthropic reply was cut off at max_tokens; estimate is incomplete"
            )
        text_block = next(
            (block for block in response.content if block.type == "text"), None
        )
        parsed = getattr(text_block, "parsed_output", None)
        if parsed is None:
            raise LLMInvalidResponse(
                f"Anthropic did not return a structured estimate "
                f"(stop_reason={response.stop_reason})"
            )
        return LLMResult(data=parsed, model=self.model, provider=self.provider)
