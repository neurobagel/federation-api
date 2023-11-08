"""Data models."""
from enum import Enum

from pydantic import BaseModel


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

class DataElementURI(str, Enum):
    """Data model for data element URIs that have available vocabulary lookups."""

    assessment = "nb:Assessment"

class VocabLabelsResponse(BaseModel):
    """Data model for response to a request for all term labels for a vocabulary."""

    vocabulary_name: str
    namespace_url: str
    namespace_prefix: str
    term_labels: dict