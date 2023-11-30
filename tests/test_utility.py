import json

import pytest
from fastapi import HTTPException

from app.api import utility as util


@pytest.fixture
def tmp_local_nb_nodes_path(tmp_path):
    """Return a temporary path to a local nodes config JSON file for testing."""
    return tmp_path / "local_nb_nodes.json"


@pytest.mark.parametrize(
    "url, expected_url",
    [
        ("https://publicnode.org", "https://publicnode.org/"),
        ("https://publicnode.org/", "https://publicnode.org/"),
    ],
)
def test_add_trailing_slash(url, expected_url):
    """Test that a trailing slash is added to a URL if it does not already have one."""
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
        ({}, {}),
    ],
)
def test_parse_nodes_as_dict(
    set_nodes, expected_nodes, tmp_local_nb_nodes_path
):
    """Test that Neurobagel nodes provided via a JSON file are correctly parsed into a list."""
    with open(tmp_local_nb_nodes_path, "w") as f:
        f.write(json.dumps(set_nodes, indent=2))

    assert util.parse_nodes_as_dict(tmp_local_nb_nodes_path) == expected_nodes


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
