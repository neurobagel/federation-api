from fastapi import APIRouter, Response, status
from pydantic import constr

from .. import crud
from ..models import CONTROLLED_TERM_REGEX, CombinedAttributeResponse

router = APIRouter(prefix="/attributes", tags=["attributes"])


@router.get("/{data_element_URI}", response_model=CombinedAttributeResponse)
async def get_terms(
    data_element_URI: constr(regex=CONTROLLED_TERM_REGEX), response: Response
):
    """When a GET request is sent, return a list dicts with the only key corresponding to controlled term of a neurobagel class and value corresponding to all the available terms."""
    response_dict = await crud.get_terms(data_element_URI)

    if response_dict["errors"]:
        response.status_code = status.HTTP_207_MULTI_STATUS

    return response_dict
