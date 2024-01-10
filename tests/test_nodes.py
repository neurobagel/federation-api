import httpx
import pytest
from fastapi import HTTPException, status

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


def test_partial_node_failures_are_handled_gracefully(
    monkeypatch, test_app, capsys
):
    """
    Test that when queries to some nodes return errors, the overall API get request still succeeds,
    the successful responses are returned along with a list of the encountered errors,
    and the failed nodes are logged to the console.
    """
    monkeypatch.setattr(
        util,
        "FEDERATION_NODES",
        {
            "https://firstpublicnode.org/": "First Public Node",
            "https://secondpublicnode.org/": "Second Public Node",
        },
    )

    def mock_send_get_request(url, params):
        if url == "https://firstpublicnode.org/query/":
            return [
                {
                    "dataset_uuid": "http://neurobagel.org/vocab/12345",
                    "dataset_name": "QPN",
                    "dataset_portal_uri": "https://rpq-qpn.ca/en/researchers-section/databases/",
                    "dataset_total_subjects": 200,
                    "num_matching_subjects": 5,
                    "records_protected": True,
                    "subject_data": "protected",
                    "image_modals": [
                        "http://purl.org/nidash/nidm#T1Weighted",
                        "http://purl.org/nidash/nidm#T2Weighted",
                    ],
                },
            ]

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="500 Server Error: Internal Server Error",
        )

    monkeypatch.setattr(util, "send_get_request", mock_send_get_request)

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
                "error": "500 Server Error: Internal Server Error",
            },
        ],
        "responses": [
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "QPN",
                "dataset_portal_uri": "https://rpq-qpn.ca/en/researchers-section/databases/",
                "dataset_total_subjects": 200,
                "num_matching_subjects": 5,
                "records_protected": True,
                "subject_data": "protected",
                "image_modals": [
                    "http://purl.org/nidash/nidm#T1Weighted",
                    "http://purl.org/nidash/nidm#T2Weighted",
                ],
                "node_name": "First Public Node",
            },
        ],
        "status": "partial success",
    }
    assert (
        "Queries to 1/2 nodes failed: ['Second Public Node']" in captured.out
    )
