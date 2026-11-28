import importlib

import pytest


@pytest.fixture
def estimation_service(main_llm):
    # Reload the module so its module-level adapter is rebuilt from the settings in main_llm
    import app.services.estimation as service

    importlib.reload(service)
    yield service
