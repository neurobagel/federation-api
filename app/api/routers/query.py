"""Router for query path operations."""

from fastapi import APIRouter, Depends, Response, status

from .. import crud
from ..models import CombinedQueryResponse, QueryModel

router = APIRouter(prefix="/query", tags=["query"])


@router.get("/", response_model=CombinedQueryResponse)
async def get_query(
    response: Response, query: QueryModel = Depends(QueryModel)
):
    """When a GET request is sent, return list of dicts corresponding to subject-level metadata aggregated by dataset."""
    response_dict = await crud.get(
        query.min_age,
        query.max_age,
        query.sex,
        query.diagnosis,
        query.is_control,
        query.min_num_imaging_sessions,
        query.min_num_phenotypic_sessions,
        query.assessment,
        query.image_modal,
        query.node_url,
    )

    if response_dict["errors"]:
        response.status_code = status.HTTP_207_MULTI_STATUS

    return response_dict
