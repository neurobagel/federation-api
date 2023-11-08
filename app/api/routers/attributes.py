from typing import List

from fastapi import APIRouter
from pydantic import constr

from .. import crud
from ..models import DataElementURI, VocabLabelsResponse

router = APIRouter(prefix="/attributes", tags=["attributes"])

@router.get("/{data_element_URI}/vocab", response_model=List[VocabLabelsResponse])
async def get_term_labels(
    data_element_URI: DataElementURI
):
    """When a GET request is sent, return a list of dicts containing the name, namespace info, and all term ID-label mappings for the vocabulary of the specified variable."""
    return await crud.get_term_labels(data_element_URI)