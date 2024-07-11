import pytest
from fastapi import HTTPException

from app.api.security import verify_token


@pytest.mark.parametrize(
    "invalid_token",
    ["Bearer faketoken", "Bearer", "faketoken", "fakescheme faketoken"],
)
def test_invalid_token_raises_error(invalid_token):
    """Test that an invalid token raises an error from the verification process."""
    with pytest.raises(HTTPException) as exc_info:
        verify_token(invalid_token)

    assert exc_info.value.status_code == 401
    assert "Invalid token" in exc_info.value.detail


@pytest.mark.parametrize(
    "invalid_auth_header",
    [{}, {"Authorization": ""}, {"badheader": "badvalue"}],
)
def test_query_fails_with_malformed_auth_header(
    test_app, monkeypatch, invalid_auth_header
):
    """Test that a request to the /query route fails with a missing or malformed authorization header."""

    # Mock verify_token function since we don't want to actually verify the token in this test
    def mock_verify_token(token):
        return None

    monkeypatch.setattr(
        "app.api.routers.query.verify_token", mock_verify_token
    )

    response = test_app.get(
        "/query/",
        headers=invalid_auth_header,
    )

    assert response.status_code == 403
