import os

import jwt
from fastapi import HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from jwt import PyJWKClient, PyJWTError

AUTH_ENABLED = os.environ.get("NB_ENABLE_AUTH", "True").lower() == "true"
CLIENT_ID = os.environ.get("NB_QUERY_CLIENT_ID", None)


def check_client_id():
    """Check if the CLIENT_ID environment variable is set."""
    # By default, if CLIENT_ID is not provided to verify_oauth2_token,
    # Google will simply skip verifying the audience claim of ID tokens.
    # This however can be a security risk, so we mandate that CLIENT_ID is set.
    if AUTH_ENABLED and CLIENT_ID is None:
        raise ValueError(
            "Authentication has been enabled (NB_ENABLE_AUTH) but the environment variable NB_QUERY_CLIENT_ID is not set. "
            "Please set NB_QUERY_CLIENT_ID to the Google client ID for your Neurobagel query tool deployment, to verify the audience claim of ID tokens."
        )


def verify_and_extract_token(token: str) -> str:
    """
    Verify and return the Google ID token with the authorization scheme stripped.
    Raise an HTTPException if the token is invalid.
    """
    google_keys_url = "https://www.googleapis.com/oauth2/v3/certs"

    # Adapted from https://developers.google.com/identity/gsi/web/guides/verify-google-id-token#python
    try:
        # Extract the token from the "Bearer" scheme
        # (See https://github.com/tiangolo/fastapi/blob/master/fastapi/security/oauth2.py#L473-L485)
        # TODO: Check also if scheme of token is "Bearer"?
        _, extracted_token = get_authorization_scheme_param(token)

        # Determine which key was used to sign the token
        # Adapted from https://pyjwt.readthedocs.io/en/stable/usage.html#retrieve-rsa-signing-keys-from-a-jwks-endpoint
        jwks_client = PyJWKClient(google_keys_url)
        signing_key = jwks_client.get_signing_key_from_jwt(extracted_token)

        # https://pyjwt.readthedocs.io/en/stable/api.html#jwt.decode
        id_info = jwt.decode(
            jwt=extracted_token,
            key=signing_key,
            options={
                "verify_signature": True,
                "require": ["aud", "iss", "exp", "iat", "nbf"],
            },
            audience=CLIENT_ID,
            issuer=["https://accounts.google.com", "accounts.google.com"],
        )

        # TODO: Remove print statement or turn into logging
        print("Token verified: ", id_info)
        return extracted_token
    except (PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
