"""Constants and utility functions for federation."""

import os
import re
import warnings

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

    node_directory_url = "https://raw.githubusercontent.com/neurobagel/menu/main/node_directory/neurobagel_public_nodes.json"
    node_directory_response = httpx.get(
        url=node_directory_url,
    )
    if node_directory_response.is_success:
        public_nodes = {
            node["ApiURL"]: node["NodeName"]
            for node in node_directory_response.json()
        }
    else:
        warnings.warn(
            f"""
            Unable to fetch directory of public Neurobagel nodes from {node_directory_url}.
            The federation API will only register the nodes defined locally for this API: {local_nodes}.

            Details of the response from the source:
            Status code {node_directory_response.status_code}
            {node_directory_response.reason_phrase}: {node_directory_response.text}
            """
        )
        public_nodes = {}

    # This step will remove any duplicate keys from the local and public node dicts, giving priority to the local nodes.
    FEDERATION_NODES.update(
        {
            **public_nodes,
            **local_nodes,
        }
    )


def check_nodes_are_recognized(node_urls: list):
    """Check that all node URLs specified in the query exist in the node index for the API instance. If not, raise an informative exception."""
    unrecognized_nodes = list(set(node_urls) - set(FEDERATION_NODES.keys()))
    if unrecognized_nodes:
        raise HTTPException(
            status_code=422,
            detail=f"Unrecognized Neurobagel node URL(s): {unrecognized_nodes}. "
            f"The following nodes are available for federation: {list(FEDERATION_NODES.keys())}",
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
