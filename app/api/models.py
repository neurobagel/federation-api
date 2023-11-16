"""Data models."""
from fastapi import Query
from pydantic import BaseModel, Field

from . import utility as util

CONTROLLED_TERM_REGEX = r"^[a-zA-Z]+[:]\S+$"


class QueryModel(BaseModel):
    """Data model and dependency for API that stores the query parameters to be accepted and validated."""

    min_age: float = None
    max_age: float = None
    sex: str = None
    diagnosis: str = None
    is_control: bool = None
    min_num_sessions: int = None
    assessment: str = None
    image_modal: str = None
    # TODO: Replace default value with union of local and public nodes once https://github.com/neurobagel/federation-api/issues/28 is merged
    node: list[str] = Field(
        Query(default=util.parse_nodes_as_list(util.NEUROBAGEL_NODES))
    )  # syntax from https://github.com/tiangolo/fastapi/issues/4445#issuecomment-1117632409
