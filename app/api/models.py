"""Data models."""
from typing import Optional, Union

from fastapi import Query
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field, root_validator

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
    # syntax from https://github.com/tiangolo/fastapi/issues/4445#issuecomment-1117632409
    node_url: list[str] = Field(
        Query(default=list(util.FEDERATION_NODES.keys()))
    )

    @root_validator
    def check_nodes_are_recognized(cls, values):
        """Check that all node URLs specified in the query exist in the node index for the API instance. If not, raise an informative exception."""
        unrecognized_nodes = list(
            set(values["node_url"]) - set(util.FEDERATION_NODES.keys())
        )
        if unrecognized_nodes:
            raise HTTPException(
                status_code=422,
                detail=f"Unrecognized Neurobagel node URL(s): {unrecognized_nodes}. "
                f"The following nodes are available for federation: {list(util.FEDERATION_NODES.keys())}",
            )
        return values


class CohortQueryResponse(BaseModel):
    """Data model for query results for one matching dataset (i.e., a cohort)."""

    node_name: str
    dataset_uuid: str
    # dataset_file_path: str  # TODO: Revisit this field once we have datasets without imaging info/sessions.
    dataset_name: str
    dataset_portal_uri: Optional[str]
    dataset_total_subjects: int
    records_protected: bool
    num_matching_subjects: int
    subject_data: Union[list[dict], str]
    image_modals: list
