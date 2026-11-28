import logging

import pytest

from app.config.logger import configure_logging, get_logger


@pytest.fixture
def restore_root_level():
    root = logging.getLogger()
    level = root.level
    yield
    root.setLevel(level)


def test_configure_logging_applies_log_level(monkeypatch, restore_root_level):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    configure_logging()

    assert logging.getLogger().level == logging.WARNING


def test_get_logger_returns_named_logger():
    assert get_logger("app.example").name == "app.example"
