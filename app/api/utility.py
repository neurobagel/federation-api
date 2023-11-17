"""Constants and utility functions for federation."""

import os
import re

import httpx
from fastapi import HTTPException

#  Neurobagel nodes
LOCAL_NODES = os.environ.get(
    "LOCAL_NB_NODES", "(https://api.neurobagel.org/, OpenNeuro)"
)
FEDERATION_NODES = {}


def parse_nodes_as_dict(nodes: str) -> list:
    """
    Transforms a string of user-defined Neurobagel nodes (from an environment variable) to a dict where the keys are the node URLs, and the values are the node names.
    It uses a regular expression to match the url, name pairs.
    Makes sure node URLs end with a slash.
    """
    pattern = re.compile(r"\((?P<url>https?://[^\s]+), (?P<label>[^\)]+)\)")
    matches = pattern.findall(nodes)
    for i in range(len(matches)):
        url, label = matches[i]
        if not url.endswith("/"):
            matches[i] = (url + "/", label)
    nodes_dict = {url: label for url, label in matches}
    return nodes_dict


async def create_federation_node_index() -> dict:
    """
    Creates an index of nodes for federation.
    Fetches the names and URLs of public Neurobagel nodes from a remote directory file, and combines them with the user-defined local nodes.
    """
    local_nodes = parse_nodes_as_dict(LOCAL_NODES)

    public_node_directory_url = "https://raw.githubusercontent.com/neurobagel/menu/main/node_directory/neurobagel_public_nodes.json"
    public_nodes = httpx.get(
        url=public_node_directory_url,
    ).json()

    # This step will remove any duplicate keys from the local and public node dicts, giving priority to the local nodes.
    FEDERATION_NODES.update(
        {
            **{node["ApiURL"]: node["NodeName"] for node in public_nodes},
            **local_nodes,
        }
    )


def send_get_request(url: str, params: list):
    """
    Makes a GET request to one or more Neurobagel nodes.

    Parameters
    ----------
    url : str
        URL of Neurobagel node API.
    params : list
        Neurobagel query parameters.

    Returns
    -------
    dict
        JSON response from Neurobagel node API.


    Raises
    ------
    HTTPException
        _description_
    """
    response = httpx.get(
        url=url,
        params=params,
        # TODO: Revisit timeout value when query performance is improved
        timeout=30.0,
        # Enable redirect following (off by default) so APIs behind a proxy can be reached
        follow_redirects=True,
    )

    if not response.is_success:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"{response.reason_phrase}: {response.text}",
        )
    return response.json()
