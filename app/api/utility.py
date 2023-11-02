"""Constants for federation."""

import os

#  Neurobagel nodes
NEUROBAGEL_NODES = os.environ.get(
    "NB_NODES", "https://api.neurobagel.org/query/"
)


def parse_nodes_as_list(nodes: str) -> list:
    """Returns user-defined Neurobagel nodes as a list, with any empty strings stripped."""
    return list(filter(None, nodes.split(" ")))
