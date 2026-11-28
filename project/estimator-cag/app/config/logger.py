import logging

from app.config.server import get_server_settings

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging() -> None:
    # Apply LOG_LEVEL to the root logger. Add a handler only if none exists yet.
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(format=LOG_FORMAT)
    root.setLevel(get_server_settings().LOG_LEVEL)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
