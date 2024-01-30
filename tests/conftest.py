import httpx
import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture()
def mock_failed_connection_httpx_get():
    async def _mock_httpx_get_with_connect_error(self, **kwargs):
        raise httpx.ConnectError("Some connection error")

    return _mock_httpx_get_with_connect_error
