import openai
from openai import AsyncOpenAI
from pydantic import ValidationError

from app.services.llm.base import DEFAULT_MAX_RETRIES, LLMAdapter, LLMResult, ModelT
from app.services.llm.errors import (
    LLMInvalidResponse,
    LLMRateLimited,
    LLMUnavailable,
)

# Per-request timeout for the OpenAI call, in seconds, so a stalled call cannot hang the server.
OPENAI_TIMEOUT_SECONDS = 300.0


class OpenAIAdapter(LLMAdapter):
    provider = "openai"

    def __init__(
        self,
        model: str,
        api_key: str,
        max_output_tokens: int,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        super().__init__(model, max_output_tokens, max_retries)
        self._client = AsyncOpenAI(api_key=api_key, max_retries=max_retries)

    async def generate(
        self, system_prompt: str, user_message: str, response_model: type[ModelT]
    ) -> LLMResult[ModelT]:
        # max_completion_tokens is the current OpenAI parameter; max_tokens is deprecated
        # and rejected by newer models. parse() sends the model as a strict JSON schema
        # and validates the reply against it.
        try:
            response = await self._client.chat.completions.parse(
                model=self.model,
                max_completion_tokens=self.max_output_tokens,
                timeout=OPENAI_TIMEOUT_SECONDS,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                response_format=response_model,
            )
        except openai.RateLimitError as exc:
            raise LLMRateLimited(f"OpenAI rate limit exceeded: {exc}") from exc
        except (
            openai.LengthFinishReasonError,
            openai.ContentFilterFinishReasonError,
            openai.APIResponseValidationError,
        ) as exc:
            raise LLMInvalidResponse(
                f"OpenAI returned an unusable response: {exc}"
            ) from exc
        except openai.OpenAIError as exc:
            raise LLMUnavailable(f"OpenAI API error: {exc}") from exc
        except ValidationError as exc:
            raise LLMInvalidResponse(
                f"OpenAI reply did not match expected schema: {exc}"
            ) from exc

        if not response.choices:
            raise LLMInvalidResponse("OpenAI returned no choices in response")
        message = response.choices[0].message
        # parsed is None after a refusal or when the reply does not fit the schema.
        # Fail here with a clear message instead of returning None.
        if message.parsed is None:
            reason = message.refusal or "no structured content"
            raise LLMInvalidResponse(
                f"OpenAI did not return a structured estimate: {reason}"
            )
        return LLMResult(data=message.parsed, model=self.model, provider=self.provider)
