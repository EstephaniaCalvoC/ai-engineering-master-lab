from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.env import ENV_FILE


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    APP_ENV: Literal["development", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"
    HOST: str = "127.0.0.1"
    PORT: int = 8001


@lru_cache
def get_server_settings() -> ServerSettings:
    return ServerSettings()
