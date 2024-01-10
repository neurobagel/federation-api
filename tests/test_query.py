import httpx
import pytest
from fastapi import status

from app.api import utility as util


@pytest.fixture()
def test_single_matching_dataset_result():
    """Valid aggregate query result for a single matching dataset."""
    return {
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
    }


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
