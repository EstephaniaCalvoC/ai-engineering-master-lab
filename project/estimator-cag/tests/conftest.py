from pathlib import Path

import pytest

INTEGRATION_DIR = Path(__file__).parent / "integration"


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run tests marked 'integration', which call real LLM APIs.",
    )


def pytest_collection_modifyitems(config, items):
    # Every test under tests/integration/ is an integration test.
    for item in items:
        if INTEGRATION_DIR in item.path.parents:
            item.add_marker(pytest.mark.integration)
    if config.getoption("--run-integration"):
        return
    skip = pytest.mark.skip(reason="integration test: pass --run-integration to run it")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
