import os

from fastapi import HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token

CLIENT_ID = os.environ.get("NB_QUERY_CLIENT_ID", None)


def verify_token(token: str):
    """Verify the Google ID token. Raise an HTTPException if the token is invalid."""
    # By default, if CLIENT_ID is not provided to verify_oauth2_token,
    # Google will simply skip verifying the audience claim of ID tokens.
    # This however can be a security risk, so we mandate that CLIENT_ID is set.
    if not CLIENT_ID:
        raise ValueError(
            "Client ID of the Neurobagel query tool must be provided to verify the audience claim of ID tokens. "
            "Please set the environment variable NB_QUERY_CLIENT_ID."
        )
    # Adapted from https://developers.google.com/identity/gsi/web/guides/verify-google-id-token#python
    try:
        # Extract the token from the "Bearer" scheme
        # (See https://github.com/tiangolo/fastapi/blob/master/fastapi/security/oauth2.py#L473-L485)
        _, param = get_authorization_scheme_param(token)
        id_info = id_token.verify_oauth2_token(
            param, requests.Request(), CLIENT_ID
        )
        # TODO: Remove print statement - just for testing
        print("Token verified: ", id_info)
    except (GoogleAuthError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
