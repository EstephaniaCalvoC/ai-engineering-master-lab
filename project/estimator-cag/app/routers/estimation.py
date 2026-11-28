from fastapi import APIRouter, HTTPException, status

from app.config.logger import get_logger
from app.schemas.estimation import EstimationRequest, EstimationResponse
from app.services.estimation import generate_estimation
from app.services.llm import (
    LLMInvalidResponse,
    LLMRateLimited,
    LLMUnavailable,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["estimation"])


@router.post("/estimate", response_model=EstimationResponse)
async def estimate(request: EstimationRequest):
    try:
        result = await generate_estimation(request.transcription)
    except LLMRateLimited as exc:
        logger.warning("LLM rate limit exceeded: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="LLM provider rate limit exceeded. Please try again later.",
        ) from exc
    except LLMUnavailable as exc:
        logger.error("LLM provider unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider is currently unavailable. Please try again later.",
        ) from exc
    except LLMInvalidResponse as exc:
        logger.error("LLM returned an invalid response: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM provider returned an invalid response.",
        ) from exc
    return result
