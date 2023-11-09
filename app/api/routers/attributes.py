from typing import List

from fastapi import APIRouter
from pydantic import constr

from .. import crud
from ..models import CONTROLLED_TERM_REGEX, DataElementURI, VocabLabelsResponse

router = APIRouter(prefix="/attributes", tags=["attributes"])


@router.get(
    "/{data_element_URI}/vocab", response_model=List[VocabLabelsResponse]
)
async def get_term_labels(data_element_URI: DataElementURI):
    """When a GET request is sent, return a list of dicts containing the name, namespace info, and all term ID-label mappings for the vocabulary of the controlled term."""
    return await crud.get_terms_labels(data_element_URI, True)


@router.get("/{data_element_URI}")
async def get_terms(data_element_URI: constr(regex=CONTROLLED_TERM_REGEX)):
    """When a GET request is sent, return a list dicts with the only key corresponding to controlled term of a neurobagel class and value corresponding to all the available terms."""
    response = await crud.get_terms_labels(data_element_URI, False)

    return response
