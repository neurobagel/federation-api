import logging

import httpx
import pytest
from fastapi import status

from app.api import utility as util

ROUTE = "/subjects"


@pytest.mark.parametrize(
    "valid_nodes",
    [
        [
            {
                "node_url": "https://firstpublicnode.org/",
                "dataset_uuids": [
                    "http://neurobagel.org/vocab/12345",
                    "http://neurobagel.org/vocab/67890",
                ],
            },
            {
                "node_url": "https://secondpublicnode.org/",
            },
        ],
        [],
        None,
    ],
)
def test_valid_nodes_do_not_error(
    test_app,
    disable_auth,
    set_valid_test_federation_nodes,
    mocked_single_matching_dataset_result,
    valid_nodes,
    monkeypatch,
    caplog,
):
    """
    Smoke test that when a valid 'nodes' list is provided, POST /subjects does not raise an error and returns a combined response.
    """
    caplog.set_level(logging.INFO)

    async def mock_httpx_request(self, method, url, **kwargs):
        return httpx.Response(
            status_code=200, json=[mocked_single_matching_dataset_result]
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", mock_httpx_request)

    response = test_app.post(ROUTE, json={"nodes": valid_nodes})

    assert response.status_code == status.HTTP_200_OK
    response = response.json()
    assert response["nodes_response_status"] == "success"
    assert response["errors"] == []
    assert len(response["responses"]) == 2
    assert "Requests to all nodes succeeded (2/2)" in caplog.text


@pytest.mark.parametrize(
    "invalid_nodes,expected_error",
    [
        (
            [
                {
                    "node_url": "https://firstpublicnode.org/",
                    "dataset_uuids": [
                        "http://neurobagel.org/vocab/12345",
                        "http://neurobagel.org/vocab/67890",
                    ],
                },
                {
                    "node_url": "https://firstpublicnode.org/",
                    "dataset_uuids": ["http://neurobagel.org/vocab/34567"],
                },
            ],
            "Duplicate node URL found",
        ),
        (
            [
                {
                    "node_url": "",
                    "dataset_uuids": ["http://neurobagel.org/vocab/12345"],
                },
            ],
            "Unrecognized Neurobagel node URL(s)",
        ),
        (
            [
                {
                    "dataset_uuids": ["http://neurobagel.org/vocab/12345"],
                },
            ],
            "Field required",
        ),
    ],
)
def test_invalid_nodes_raise_error(
    test_app,
    disable_auth,
    set_valid_test_federation_nodes,
    invalid_nodes,
    expected_error,
):
    """Test that when an invalid 'nodes' list is provided, POST /subjects raises a 422 error with an appropriate message."""
    response = test_app.post(ROUTE, json={"nodes": invalid_nodes})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert expected_error in response.text


def test_extra_query_fields_raise_error(
    test_app,
    disable_auth,
    set_valid_test_federation_nodes,
):
    """Test that when extra fields are provided in the query, POST /subjects raises a 422 error with an appropriate message."""
    response = test_app.post(
        ROUTE,
        json={
            "nodes": [
                {
                    "node_url": "https://firstpublicnode.org/",
                }
            ],
            "invalid_extra_field": "unexpected_value",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert all(
        msg in response.text for msg in ["invalid_extra_field", "Extra inputs"]
    )


def test_node_requests_contain_intended_dataset_uuids(
    test_app,
    disable_auth,
    set_valid_test_federation_nodes,
    mocked_single_matching_dataset_result,
    monkeypatch,
):
    captured_requests = []

    async def mock_send_request(method, url, **kwargs):
        captured_requests.append({"url": url, "body": kwargs["body"]})
        # Return valid dummy response since we only care about the outgoing request content here
        return [mocked_single_matching_dataset_result]

    federated_query = {
        "nodes": [
            {
                "node_url": "https://firstpublicnode.org/",
                "dataset_uuids": [
                    "http://neurobagel.org/vocab/ds-001",
                    "http://neurobagel.org/vocab/ds-002",
                ],
            },
            {
                "node_url": "https://secondpublicnode.org/",
                "dataset_uuids": [
                    "http://neurobagel.org/vocab/ds-003",
                ],
            },
        ]
    }

    monkeypatch.setattr(util, "send_request", mock_send_request)

    test_app.post(
        ROUTE,
        json=federated_query,
    )

    assert len(captured_requests) == 2
    assert (
        captured_requests[0]["url"] == "https://firstpublicnode.org/subjects"
    )
    assert captured_requests[0]["body"]["dataset_uuids"] == [
        "http://neurobagel.org/vocab/ds-001",
        "http://neurobagel.org/vocab/ds-002",
    ]
    assert (
        captured_requests[1]["url"] == "https://secondpublicnode.org/subjects"
    )
    assert captured_requests[1]["body"]["dataset_uuids"] == [
        "http://neurobagel.org/vocab/ds-003",
    ]
