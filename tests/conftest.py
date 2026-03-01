"""Shared fixtures for the test suite."""

import pytest
import time
import threading
from tourism_dashboard.app import create_app


@pytest.fixture(scope="module")
def dash_app():
    """Fresh Dash app instance."""
    return create_app()


@pytest.fixture(scope="module")
def dash_server(dash_app):
    """Run the Dash app on a background thread so selenium can hit it."""
    port = 8052
    t = threading.Thread(
        target=dash_app.run,
        kwargs={"debug": False, "port": port},
        daemon=True,
    )
    t.start()
    time.sleep(2)  # give it a moment to boot
    yield f"http://127.0.0.1:{port}"
