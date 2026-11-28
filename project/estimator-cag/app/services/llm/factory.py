from app.services.llm.anthropic_adapter import AnthropicAdapter
from app.services.llm.base import DEFAULT_MAX_RETRIES, LLMAdapter
from app.services.llm.openai_adapter import OpenAIAdapter

# Keys must match the values allowed by LLMProviderName in app/config/service.py.
_ADAPTERS: dict[str, type[LLMAdapter]] = {
    AnthropicAdapter.provider: AnthropicAdapter,
    OpenAIAdapter.provider: OpenAIAdapter,
}


def build_adapter(
    provider: str,
    model: str,
    api_key: str,
    max_output_tokens: int,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> LLMAdapter:
    adapter_cls = _ADAPTERS.get(provider)
    if adapter_cls is None:
        # Settings already reject unknown providers; this guards direct callers.
        raise ValueError(f"Unsupported LLM provider: {provider}")
    return adapter_cls(
        model=model,
        api_key=api_key,
        max_output_tokens=max_output_tokens,
        max_retries=max_retries,
    )
