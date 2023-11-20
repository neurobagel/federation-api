import os
from contextlib import nullcontext as does_not_raise

import pytest
from fastapi import HTTPException

from app.api import utility as util


@pytest.mark.parametrize(
    "set_nodes, expected_nodes",
    [
        (
            "(https://firstnode.neurobagel.org/query, firstnode)",
            {"https://firstnode.neurobagel.org/query/": "firstnode"},
        ),
        (
            "(https://firstnode.neurobagel.org/query/, firstnode) (https://secondnode.neurobagel.org/query, secondnode)",
            {
                "https://firstnode.neurobagel.org/query/": "firstnode",
                "https://secondnode.neurobagel.org/query/": "secondnode",
            },
        ),
        (
            "(firstnode.neurobagel.org/query/, firstnode) (https://secondnode.neurobagel.org/query, secondnode)",
            {
                "https://secondnode.neurobagel.org/query/": "secondnode",
            },
        ),
        (
            "( , firstnode) (https://secondnode.neurobagel.org/query, secondnode)",
            {
                "https://secondnode.neurobagel.org/query/": "secondnode",
            },
        ),
    ],
)
def test_parse_nodes_as_dict(monkeypatch, set_nodes, expected_nodes):
    """Test that Neurobagel node URLs provided in a string environment variable are correctly parsed into a list."""
    monkeypatch.setenv("LOCAL_NB_NODES", set_nodes)
    assert sorted(
        util.parse_nodes_as_dict(
            os.environ.get(
                "LOCAL_NB_NODES", "https://api.neurobagel.org/query/"
            )
        )
    ) == sorted(expected_nodes)


@pytest.mark.parametrize(
    "node_url_list, expectation, unrecognized_urls",
    [
        (["https://firstknownnode.org/"], does_not_raise(), None),
        ([], does_not_raise(), None),
        (
            ["https://firstknownnode.org/", "https://mysterynode.org/"],
            pytest.raises(HTTPException),
            "['https://mysterynode.org/']",
        ),
        (
            ["https://mysterynode.org/", "https://unknownnode.org/"],
            pytest.raises(HTTPException),
            "['https://mysterynode.org/', 'https://unknownnode.org/']",
        ),
    ],
)
def test_check_nodes_are_recognized(
    monkeypatch, node_url_list, expectation, unrecognized_urls
):
    """Test that function correctly errors out when any node URL not found in the federation node index is present, but not otherwise."""
    mock_federation_nodes = {
        "https://firstknownnode.org/": "My First Node",
        "https://secondknownnode.org/": "My Second Node",
    }

    monkeypatch.setattr(util, "FEDERATION_NODES", mock_federation_nodes)

    with expectation as exc_info:
        util.check_nodes_are_recognized(node_url_list)
    if exc_info is not None:
        assert (
            f"Unrecognized Neurobagel node URL(s): {unrecognized_urls}"
            in exc_info.value.detail
        )
