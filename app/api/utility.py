"""Constants for federation."""

import os

#  Neurobagel nodes
NEUROBAGEL_NODES = os.environ.get(
    "NB_NODES", "http://api.neurobagel.org/query/"
)


def parse_nodes_as_list(nodes: str) -> list:
    """Returns user-defined Neurobagel nodes as a list."""
    return list(nodes.split(" "))
