from opentelemetry import trace

from app.config import get_service_settings
from app.config.logger import get_logger
from app.config.tracing import get_tracer
from app.context.estimation_system_prompt import (
    ACTIVE_PROMPT_VERSION,
    build_system_prompt,
    load_system_prompt,
)
from app.schemas.estimation import EstimationOutputData
from app.services.llm import LLMRateLimited, LLMUnavailable, build_adapter

logger = get_logger(__name__)
settings = get_service_settings()
tracer = get_tracer(__name__)

llm = build_adapter(
    provider=settings.MAIN_LLM_PROVIDER,
    model=settings.MAIN_LLM_MODEL,
    api_key=settings.main_api_key.get_secret_value(),
    max_output_tokens=settings.MAX_OUTPUT_TOKENS,
    max_retries=settings.LLM_MAX_RETRIES,
)

fallback_llm = (
    build_adapter(
        provider=settings.FALLBACK_LLM_PROVIDER,
        model=settings.FALLBACK_LLM_MODEL,
        api_key=settings.fallback_api_key.get_secret_value(),
        max_output_tokens=settings.MAX_OUTPUT_TOKENS,
        max_retries=settings.LLM_MAX_RETRIES,
    )
    if settings.FALLBACK_LLM_PROVIDER
    and settings.FALLBACK_LLM_MODEL
    and settings.fallback_api_key
    else None
)

# Loaded once at import, so a missing or invalid prompt file fails at startup
active_prompt = load_system_prompt(ACTIVE_PROMPT_VERSION)


def format_hours(hours: float) -> str:
    # 40.0 -> "40", 17.5 -> "17.5"
    return f"{hours:g}"


def render_estimation(estimate: EstimationOutputData) -> str:
    """Render the structured estimate as the plain-text `estimation` field."""
    # Tasks are numbered continuously across phases
    n = 0
    phase_blocks = []
    for phase in estimate.phases:
        lines = [f"**{phase.name}** ({format_hours(phase.hours)} hours)"]
        for task in phase.tasks:
            n += 1
            lines.append(f"{n}. {task.name}: {format_hours(task.hours)} hours")
        phase_blocks.append("\n".join(lines))
    tasks = "\n\n".join(phase_blocks)
    team = " + ".join(
        f"{member.count} {member.role}" + (" (part-time)" if member.part_time else "")
        for member in estimate.team
    )
    duration = estimate.duration
    weeks = (
        f"{duration.min_weeks} weeks"
        if duration.min_weeks == duration.max_weeks
        else f"{duration.min_weeks}–{duration.max_weeks} weeks"
    )
    return (
        "## Estimate\n"
        "### Task breakdown:\n"
        f"{tasks}\n\n"
        f"**Total estimate: {format_hours(estimate.total_hours)} hours**\n"
        f"**Recommended team: {team}**\n"
        f"**Estimated duration: {weeks}**\n"
    )


@tracer.chain
async def generate_estimation(transcription: str) -> dict:
    span = trace.get_current_span()
    span.set_attribute("system_prompt_version", active_prompt.version)
    system_prompt = build_system_prompt(active_prompt)

    fallback_used = False
    try:
        result = await llm.generate(system_prompt, transcription, EstimationOutputData)
    except (LLMRateLimited, LLMUnavailable) as exc:
        if fallback_llm is None:
            raise
        logger.warning(
            "Main LLM (%s/%s) failed with %s; falling back to %s/%s",
            llm.provider,
            llm.model,
            type(exc).__name__,
            fallback_llm.provider,
            fallback_llm.model,
        )
        result = await fallback_llm.generate(
            system_prompt, transcription, EstimationOutputData
        )
        fallback_used = True

    span.set_attribute("llm.fallback_used", fallback_used)
    estimate = result.data
    return {
        "estimation": render_estimation(estimate),
        "estimation_output_data": estimate,
        "model": result.model,
        "provider": result.provider,
        "system_prompt_version": active_prompt.version,
        "fallback_used": fallback_used,
    }
