import json

import httpx
import pytest
from fastapi import HTTPException

from app.api import utility as util


@pytest.mark.parametrize(
    "url, expected_url",
    [
        ("https://publicnode.org", "https://publicnode.org/"),
        ("https://publicnode.org/", "https://publicnode.org/"),
    ],
)
def test_add_trailing_slash(url, expected_url):
    """
    Test that a trailing slash is added to a
    URL if it does not already have one.
    """
    assert util.add_trailing_slash(url) == expected_url


@pytest.mark.parametrize(
    "set_nodes, expected_nodes",
    [
        (
            {
                "ApiURL": "http://firstnode.neurobagel.org/query",
                "NodeName": "firstnode",
            },
            {"http://firstnode.neurobagel.org/query/": "firstnode"},
        ),
        (
            [
                {
                    "ApiURL": "http://firstnode.neurobagel.org/query",
                    "NodeName": "firstnode",
                }
            ],
            {"http://firstnode.neurobagel.org/query/": "firstnode"},
        ),
        (
            [
                {
                    "ApiURL": "https://firstnode.neurobagel.org/query/",
                    "NodeName": "firstnode",
                },
                {
                    "ApiURL": "https://secondnode.neurobagel.org/query",
                    "NodeName": "secondnode",
                },
            ],
            {
                "https://firstnode.neurobagel.org/query/": "firstnode",
                "https://secondnode.neurobagel.org/query/": "secondnode",
            },
        ),
    ],
)
def test_parse_nodes_as_dict(set_nodes, expected_nodes, tmp_path):
    """Test that Neurobagel nodes provided via a JSON file are correctly parsed into a list."""
    # First create a temporary input config file for the test to read
    with open(tmp_path / "local_nb_nodes.json", "w") as f:
        f.write(json.dumps(set_nodes, indent=2))

    assert (
        util.parse_nodes_as_dict(tmp_path / "local_nb_nodes.json")
        == expected_nodes
    )


def test_recognized_query_nodes_do_not_raise_error(monkeypatch):
    """Test that node URLs found in the federation node index do not raise an error."""
    monkeypatch.setattr(
        util,
        "FEDERATION_NODES",
        {
            "https://firstknownnode.org/": "My First Node",
            "https://secondknownnode.org/": "My Second Node",
        },
    )

    util.check_nodes_are_recognized(["https://firstknownnode.org/"])


@pytest.mark.parametrize(
    "node_url_list, unrecognized_urls",
    [
        (
            ["https://firstknownnode.org/", "https://mysterynode.org/"],
            "['https://mysterynode.org/']",
        ),
        (
            ["https://mysterynode.org/", "https://unknownnode.org/"],
            "['https://mysterynode.org/', 'https://unknownnode.org/']",
        ),
    ],
)
def test_unrecognized_query_nodes_raise_error(
    monkeypatch, node_url_list, unrecognized_urls
):
    """Test that we raise a helpful error when the user is trying to query an unknown node."""
    monkeypatch.setattr(
        util,
        "FEDERATION_NODES",
        {
            "https://firstknownnode.org/": "My First Node",
            "https://secondknownnode.org/": "My Second Node",
        },
    )

    with pytest.raises(HTTPException) as exc_info:
        util.check_nodes_are_recognized(node_url_list)
    assert (
        f"Unrecognized Neurobagel node URL(s): {unrecognized_urls}"
        in exc_info.value.detail
    )


@pytest.mark.parametrize(
    "raw_url_list, expected_url_list",
    [
        (["https://firstknownnode.org"], ["https://firstknownnode.org/"]),
        (
            ["https://firstknownnode.org", "https://secondknownnode.org/"],
            ["https://firstknownnode.org/", "https://secondknownnode.org/"],
        ),
        (
            ["", "https://secondknownnode.org"],
            ["https://secondknownnode.org/"],
        ),
        (
            [
                "https://secondknownnode.org/",
                "https://firstknownnode.org",
                "https://secondknownnode.org/",
            ],
            ["https://secondknownnode.org/", "https://firstknownnode.org/"],
        ),
        ([], ["https://firstknownnode.org/", "https://secondknownnode.org/"]),
    ],
)
def test_validate_query_node_url_list(
    monkeypatch, raw_url_list, expected_url_list
):
    """Test that provided URLs are deduplicated, get a trailing slash, and default to FEDERATION_NODES if none are provided."""
    monkeypatch.setattr(
        util,
        "FEDERATION_NODES",
        {
            "https://firstknownnode.org/": "My First Node",
            "https://secondknownnode.org/": "My Second Node",
        },
    )

    assert util.validate_query_node_url_list(raw_url_list) == expected_url_list


@pytest.mark.parametrize(
    "raw_nodes, nodes_as_dicts, expected_nodes",
    [
        (
            [
                {
                    "node_url": "https://firstknownnode.org/node",
                    "dataset_uuids": [
                        "http://neurobagel.org/vocab/12345",
                        "http://neurobagel.org/vocab/67890",
                    ],
                },
                {
                    "node_url": "https://secondknownnode.org/node",
                    "dataset_uuids": [
                        "http://neurobagel.org/vocab/23456",
                        "http://neurobagel.org/vocab/34567",
                    ],
                },
            ],
            True,
            [
                {
                    "node_url": "https://firstknownnode.org/node/",
                    "dataset_uuids": [
                        "http://neurobagel.org/vocab/12345",
                        "http://neurobagel.org/vocab/67890",
                    ],
                },
                {
                    "node_url": "https://secondknownnode.org/node/",
                    "dataset_uuids": [
                        "http://neurobagel.org/vocab/23456",
                        "http://neurobagel.org/vocab/34567",
                    ],
                },
            ],
        ),
        (
            [],
            True,
            [
                {
                    "node_url": "https://firstknownnode.org/node/",
                },
                {
                    "node_url": "https://secondknownnode.org/node/",
                },
            ],
        ),
        (
            None,
            True,
            [
                {
                    "node_url": "https://firstknownnode.org/node/",
                },
                {
                    "node_url": "https://secondknownnode.org/node/",
                },
            ],
        ),
        (
            [
                "https://firstknownnode.org/node",
                "https://secondknownnode.org/node",
            ],
            False,
            [
                "https://firstknownnode.org/node/",
                "https://secondknownnode.org/node/",
            ],
        ),
        (
            [],
            False,
            [
                "https://firstknownnode.org/node/",
                "https://secondknownnode.org/node/",
            ],
        ),
        (
            None,
            False,
            [
                "https://firstknownnode.org/node/",
                "https://secondknownnode.org/node/",
            ],
        ),
    ],
)
def test_validate_queried_nodes(
    monkeypatch, raw_nodes, nodes_as_dicts, expected_nodes
):
    """
    Test that a trailing slash is added to node URLs, dataset UUIDs are preserved (when provided),
    and the default list of all known federation nodes is used if none are specified.
    Tests both dict format (for /subjects) and string format (for /datasets).
    """
    monkeypatch.setattr(
        util,
        "FEDERATION_NODES",
        {
            "https://firstknownnode.org/node/": "My First Node",
            "https://secondknownnode.org/node/": "My Second Node",
        },
    )

    assert (
        util.validate_queried_nodes(raw_nodes, nodes_as_dicts)
        == expected_nodes
    )


@pytest.mark.parametrize(
    "set_nodes,expected_nodes",
    [
        (
            {
                "IMakeMyOwnRules": "http://firstnode.neurobagel.org/query",
                "WhatAreSchemas": "firstnode",
            },
            {},
        ),
        (
            {
                "ApiURL": "this.is.not.a.url",
                "NodeName": "firstnode",
            },
            {},
        ),
        (
            [
                {
                    "ApiURL": "https://firstnode.neurobagel.org/query/",
                    "NodeName": "firstnode",
                },
                {
                    "ApiURL": "invalidurl",
                    "NodeName": "secondnode",
                },
            ],
            {
                "https://firstnode.neurobagel.org/query/": "firstnode",
            },
        ),
        ({}, {}),
    ],
)
def test_schema_invalid_nodes_raise_warning(
    set_nodes, expected_nodes, tmp_path
):
    """
    If the JSON is valid but parts of the schema are invalid, expect to raise a warning
    and only return the parts that fit the schema.
    """
    # TODO: split this test into the warning and the output
    # First create a temporary input config file for the test to read
    with open(tmp_path / "local_nb_nodes.json", "w") as f:
        f.write(json.dumps(set_nodes, indent=2))

    with pytest.warns(
        UserWarning, match=r"Some of the nodes in the JSON are invalid.*"
    ):
        nodes = util.parse_nodes_as_dict(tmp_path / "local_nb_nodes.json")

    assert nodes == expected_nodes


def test_invalid_json_raises_warning(tmp_path):
    """Ensure that an invalid JSON file raises a warning but doesn't crash the app."""

    with open(tmp_path / "local_nb_nodes.json", "w") as f:
        f.write("this is not valid JSON")

    with pytest.warns(UserWarning, match="You provided an invalid JSON"):
        util.parse_nodes_as_dict(tmp_path / "local_nb_nodes.json")


def test_empty_json_does_not_error(tmp_path):
    """Ensure that an empty JSON file does not raise an error."""

    with open(tmp_path / "local_nb_nodes.json", "w") as f:
        f.write("")

    assert util.parse_nodes_as_dict(tmp_path / "local_nb_nodes.json") == {}


@pytest.mark.asyncio
async def test_federate_only_local_nodes(tmp_path, monkeypatch):
    """Ensure that the API only federates local nodes when NB_FEDERATE_REMOTE_PUBLIC_NODES env var is set to False."""

    local_nodes = {
        "https://firstlocalnode.org/": "First Local Node",
        "https://secondlocalnode.org/": "Second Local Node",
    }

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
            ],
        )

    monkeypatch.setattr(util, "parse_nodes_as_dict", mock_parse_nodes_as_dict)
    monkeypatch.setattr(httpx, "get", mock_httpx_get)
    monkeypatch.setattr(
        util, "IS_FEDERATE_REMOTE_PUBLIC_NODES", util.EnvVar("", False)
    )

    await util.create_federation_node_index()

    assert util.FEDERATION_NODES == local_nodes


@pytest.mark.parametrize(
    "node_response, expected_is_valid_result, expected_error",
    [
        ({"nb:Assessment": []}, True, ""),
        (
            HTTPException(status_code=404, detail="Not found"),
            False,
            "Not found",
        ),
        (
            {
                "nb:Assessment": [
                    {
                        "TermURL": "snomed:273640001",
                        "Label": "National adult reading test",
                    },
                    {
                        "TermURL": "snomed:859351000000102",
                        "Label": "Montreal cognitive assessment",
                    },
                ]
            },
            True,
            "",
        ),
        ([], False, "Unexpected response format received from node"),
        (
            {"nb:WrongKey": []},
            False,
            "Unexpected response format received from node",
        ),
    ],
)
def test_is_valid_dict_response(
    node_response, expected_is_valid_result, expected_error
):
    """
    Test that node responses are correctly validated for expected keys,
    with appropriate messages for unexpected responses or errors.
    """
    assert util.is_valid_dict_response(
        response=node_response, find_key="nb:Assessment"
    ) == (expected_is_valid_result, expected_error)
