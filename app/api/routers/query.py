"""Router for query path operations."""

from fastapi import APIRouter, Depends

from .. import crud
from ..models import QueryModel

router = APIRouter(prefix="/query", tags=["query"])


# TODO: update to change the logic once crud is modified


@router.get("/")
async def get_query(query: QueryModel = Depends(QueryModel)):
    """When a GET request is sent, return list of dicts corresponding to subject-level metadata aggregated by dataset."""
    response = await crud.get(
        query.min_age,
        query.max_age,
        query.sex,
        query.diagnosis,
        query.is_control,
        query.min_num_sessions,
        query.assessment,
        query.image_modal,
    )

    return response
