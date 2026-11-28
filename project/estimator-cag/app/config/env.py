import os
import re

from dotenv import dotenv_values

ENV_FILE = ".env"
ENV_VAR_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def read_env_var(name: str) -> str | None:
    # The process environment wins over .env, same as pydantic-settings
    value = os.environ.get(name)
    if value is None:
        value = dotenv_values(ENV_FILE).get(name)
    return value or None
