import httpx
import pytest
from starlette.testclient import TestClient

from app.api import utility as util
from app.main import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture(scope="function")
def set_valid_test_federation_nodes(monkeypatch):
    monkeypatch.setattr(
        util,
        "FEDERATION_NODES",
        {
            "https://firstpublicnode.org/": "First Public Node",
            "https://secondpublicnode.org/": "Second Public Node",
        },
    )


@pytest.fixture()
def mock_failed_connection_httpx_get():
    async def _mock_httpx_get_with_connect_error(self, **kwargs):
        raise httpx.ConnectError("Some connection error")

    return _mock_httpx_get_with_connect_error
