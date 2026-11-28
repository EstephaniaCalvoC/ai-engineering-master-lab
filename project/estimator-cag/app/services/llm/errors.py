class LLMError(Exception):
    """Base error for failures when calling an LLM provider."""


class LLMUnavailable(LLMError):
    """The LLM provider could not be reached, timed out, or returned an API error."""


class LLMRateLimited(LLMError):
    """The LLM provider rejected the request because of rate limits (HTTP 429)."""


class LLMInvalidResponse(LLMError):
    """The LLM provider returned a response that could not be parsed or validated."""
