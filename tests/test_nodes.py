import httpx
import pytest
from fastapi import status

from app.api import utility as util


@pytest.mark.parametrize(
    "local_nodes",
    [
        {"https://mylocalnode.org/": "Local Node"},
        {
            "https://mylocalnode.org/": "Local Node",
            "https://firstpublicnode.org/": "First Public Node",
        },
    ],
)
def test_nodes_discovery_endpoint(test_app, monkeypatch, local_nodes):
    """Test that a federation node index is correctly created from locally set and remote node lists."""

    def mock_parse_nodes_as_dict(path):
        return local_nodes

    def mock_httpx_get(**kwargs):
        return httpx.Response(
            status_code=200,
            json=[
                {
                    "NodeName": "First Public Node",
                    "ApiURL": "https://firstpublicnode.org",
                },
                {
                    "NodeName": "Second Public Node",
                    "ApiURL": "https://secondpublicnode.org",
                },
            ],
        )

    monkeypatch.setattr(util, "parse_nodes_as_dict", mock_parse_nodes_as_dict)
    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with test_app:
        response = test_app.get("/nodes/")
        assert util.FEDERATION_NODES == {
            "https://firstpublicnode.org/": "First Public Node",
            "https://secondpublicnode.org/": "Second Public Node",
            "https://mylocalnode.org/": "Local Node",
        }
        assert response.json() == [
            {
                "NodeName": "First Public Node",
                "ApiURL": "https://firstpublicnode.org/",
            },
            {
                "NodeName": "Second Public Node",
                "ApiURL": "https://secondpublicnode.org/",
            },
            {"NodeName": "Local Node", "ApiURL": "https://mylocalnode.org/"},
        ]


def test_failed_public_nodes_fetching_raises_warning(test_app, monkeypatch):
    """Test that when request for remote list of public nodes fails, an informative warning is raised and the federation node index only includes local nodes."""

    def mock_parse_nodes_as_dict(path):
        return {"https://mylocalnode.org/": "Local Node"}

    def mock_httpx_get(**kwargs):
        return httpx.Response(
            status_code=404, json={}, text="Some error message"
        )

    monkeypatch.setattr(util, "parse_nodes_as_dict", mock_parse_nodes_as_dict)
    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.warns(UserWarning) as w:
        with test_app:
            response = test_app.get("/nodes/")
            assert util.FEDERATION_NODES == {
                "https://mylocalnode.org/": "Local Node"
            }
            assert response.json() == [
                {
                    "NodeName": "Local Node",
                    "ApiURL": "https://mylocalnode.org/",
                }
            ]

    assert len(w) == 1
    for warn_substr in [
        "Unable to fetch directory of public Neurobagel nodes",
        "Federation will be limited to the nodes defined locally for this API: {'https://mylocalnode.org/': 'Local Node'}",
    ]:
        assert warn_substr in w[0].message.args[0]


def test_unset_local_nodes_raises_warning(test_app, monkeypatch):
    """Test that when no local nodes are set, an informative warning is raised and the federation node index only includes remote nodes."""

    def mock_parse_nodes_as_dict(path):
        return {}

    def mock_httpx_get(**kwargs):
        return httpx.Response(
            status_code=200,
            json=[
                {
                    "NodeName": "First Public Node",
                    "ApiURL": "https://firstpublicnode.org",
                },
                {
                    "NodeName": "Second Public Node",
                    "ApiURL": "https://secondpublicnode.org",
                },
            ],
        )

    monkeypatch.setattr(util, "parse_nodes_as_dict", mock_parse_nodes_as_dict)
    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.warns(UserWarning) as w:
        with test_app:
            response = test_app.get("/nodes/")
            assert util.FEDERATION_NODES == {
                "https://firstpublicnode.org/": "First Public Node",
                "https://secondpublicnode.org/": "Second Public Node",
            }
            assert response.json() == [
                {
                    "NodeName": "First Public Node",
                    "ApiURL": "https://firstpublicnode.org/",
                },
                {
                    "NodeName": "Second Public Node",
                    "ApiURL": "https://secondpublicnode.org/",
                },
            ]

    assert len(w) == 1
    assert "No local Neurobagel nodes defined or found" in w[0].message.args[0]


def test_no_available_nodes_raises_error(monkeypatch, test_app):
    """Test that when no local or remote nodes are available, an informative error is raised."""

    def mock_parse_nodes_as_dict(path):
        return {}

    def mock_httpx_get(**kwargs):
        return httpx.Response(
            status_code=404, json={}, text="Some error message"
        )

    monkeypatch.setattr(util, "parse_nodes_as_dict", mock_parse_nodes_as_dict)
    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.warns(UserWarning) as w, pytest.raises(
        RuntimeError
    ) as exc_info:
        with test_app:
            pass

    # Two warnings are expected, one for the failed GET request for public nodes, and one for the lack of local nodes.
    assert len(w) == 2
    assert (
        "No local or public Neurobagel nodes available for federation"
        in str(exc_info.value)
    )


def test_partial_node_failure_responses_are_handled_gracefully(
    monkeypatch, test_app, capsys, test_single_matching_dataset_result
):
    """
    Test that when queries to some nodes return errors, the overall API get request still succeeds,
    the successful responses are returned along with a list of the encountered errors, and the failed nodes are logged to the console.
    """
    monkeypatch.setattr(
        util,
        "FEDERATION_NODES",
        {
            "https://firstpublicnode.org/": "First Public Node",
            "https://secondpublicnode.org/": "Second Public Node",
        },
    )

    def mock_httpx_get(**kwargs):
        if kwargs["url"] == "https://firstpublicnode.org/query/":
            return httpx.Response(
                status_code=200, json=[test_single_matching_dataset_result]
            )

        return httpx.Response(
            status_code=500, json={}, text="Some internal server error"
        )

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.warns(
        UserWarning,
        match=r"Second Public Node \(https://secondpublicnode.org/\) did not succeed",
    ):
        response = test_app.get("/query/")
        captured = capsys.readouterr()

    assert response.status_code == status.HTTP_207_MULTI_STATUS
    assert response.json() == {
        "errors": [
            {
                "NodeName": "Second Public Node",
                "error": "Internal Server Error: Some internal server error",
            },
        ],
        "responses": [
            {
                **test_single_matching_dataset_result,
                "node_name": "First Public Node",
            },
        ],
        "nodes_response_status": "partial success",
    }
    assert (
        "Queries to 1/2 nodes failed: ['Second Public Node']" in captured.out
    )


def test_partial_node_connection_failures_are_handled_gracefully(
    monkeypatch, test_app, capsys, test_single_matching_dataset_result
):
    """
    Test that when requests to some nodes fail (e.g., if API is unreachable), the overall API get request still succeeds,
    the successful responses are returned along with a list of the encountered errors, and the failed nodes are logged to the console.
    """
    monkeypatch.setattr(
        util,
        "FEDERATION_NODES",
        {
            "https://firstpublicnode.org/": "First Public Node",
            "https://secondpublicnode.org/": "Second Public Node",
        },
    )

    def mock_httpx_get(**kwargs):
        if kwargs["url"] == "https://firstpublicnode.org/query/":
            return httpx.Response(
                status_code=200, json=[test_single_matching_dataset_result]
            )

        raise httpx.ConnectError("Some connection error")

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.warns(
        UserWarning,
        match=r"Second Public Node \(https://secondpublicnode.org/\) did not succeed",
    ):
        response = test_app.get("/query/")
        captured = capsys.readouterr()

    assert response.status_code == status.HTTP_207_MULTI_STATUS
    assert response.json() == {
        "errors": [
            {
                "NodeName": "Second Public Node",
                "error": "Request failed due to a network error or because the node API cannot be reached: Some connection error",
            },
        ],
        "responses": [
            {
                **test_single_matching_dataset_result,
                "node_name": "First Public Node",
            },
        ],
        "nodes_response_status": "partial success",
    }
    assert (
        "Queries to 1/2 nodes failed: ['Second Public Node']" in captured.out
    )

    # TODO: test for all nodes failed, or succeeded
