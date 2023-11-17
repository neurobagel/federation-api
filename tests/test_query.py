import pytest

from app.api import crud


@pytest.fixture
def mock_invalid_get():
    """Mock get function that does not return any response (for testing invalid parameter values)."""

    async def mockreturn(
        min_age,
        max_age,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        assessment,
        image_modal,
        node_urls,
    ):
        return None

    return mockreturn


@pytest.mark.parametrize(
    "invalid_node_url_list",
    [
        [
            "https://api.neurobagel.org/",
            "https://mysterynode.org/",
        ],  # can probably change this to set an environment variable
        ["http://unknownnode.org", "https://mysterynode.org/"],
    ],
)
def test_get_invalid_node_urls(
    test_app, mock_invalid_get, monkeypatch, invalid_node_url_list
):
    """Given a node URL list that contains URL(s) not recognized by the API instance, returns an informative 422 error response."""

    monkeypatch.setattr(crud, "get", mock_invalid_get)

    response = test_app.get(
        f"/query/?node_url={invalid_node_url_list[0]}&node_url={invalid_node_url_list[1]}"
    )
    assert response.status_code == 422
    assert "Unrecognized Neurobagel node URL(s)" in response.text
