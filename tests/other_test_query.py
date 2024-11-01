import pytest

from app.api import crud
from app.api import utility as util
from app.api.models import QueryModel


@pytest.mark.anyio
@pytest.mark.parametrize(
    "valid_node_url_list",
    [
        ["https://firstknownnode.org"],
        ["https://firstknownnode.org", "https://secondknownnode.org/"],
        ["", "https://secondknownnode.org"],
    ],
)
async def test_get_with_valid_node_urls(monkeypatch, valid_node_url_list):
    """Given a node URL list that contains URL(s) not recognized by the API instance, returns an informative 422 error response."""
    mock_federation_nodes = {
        "https://firstknownnode.org/": "My First Node",
        "https://secondknownnode.org/": "My Second Node",
    }

    def mock_send_get_request(url, params):
        return []

    monkeypatch.setattr(util, "FEDERATION_NODES", mock_federation_nodes)
    monkeypatch.setattr(util, "send_get_request", mock_send_get_request)

    params = {param: None for param in list(QueryModel.__fields__.keys())}
    del params["node_url"]
    results = await crud.get(node_urls=valid_node_url_list, **params)
    assert results == []
