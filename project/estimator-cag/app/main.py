from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.config import get_server_settings
from app.config.logger import configure_logging, get_logger
from app.config.tracing import configure_tracing, shutdown_tracing

settings = get_server_settings()
configure_logging()
logger = get_logger(__name__)

# Register Arize tracing and OpenInference instrumentors before importing routers,
# since app.services.estimation instantiates the LLM client at import time.
configure_tracing()

from app.routers import estimation


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    shutdown_tracing()


app = FastAPI(
    title="AI Software Development Estimator",
    description="Software estimation system with CAG Architecture",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(estimation.router)


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    logger.info(
        "Starting server on %s:%s (%s)", settings.HOST, settings.PORT, settings.APP_ENV
    )
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_ENV == "development",
    )
