import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture()
def test_single_matching_dataset_result():
    """Valid aggregate query result for a single matching dataset."""
    return {
        "dataset_uuid": "http://neurobagel.org/vocab/12345",
        "dataset_name": "QPN",
        "dataset_portal_uri": "https://rpq-qpn.ca/en/researchers-section/databases/",
        "dataset_total_subjects": 200,
        "num_matching_subjects": 5,
        "records_protected": True,
        "subject_data": "protected",
        "image_modals": [
            "http://purl.org/nidash/nidm#T1Weighted",
            "http://purl.org/nidash/nidm#T2Weighted",
        ],
    }
