import os

import jwt
from fastapi import HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from jwt import PyJWKClient, PyJWTError

AUTH_ENABLED = os.environ.get("NB_ENABLE_AUTH", "True").lower() == "true"
CLIENT_ID = os.environ.get("NB_QUERY_CLIENT_ID", None)


def check_client_id():
    """Check if the CLIENT_ID environment variable is set."""
    # The CLIENT_ID is needed to verify the audience claim of ID tokens.
    if AUTH_ENABLED and CLIENT_ID is None:
        raise ValueError(
            "Authentication has been enabled (NB_ENABLE_AUTH) but the environment variable NB_QUERY_CLIENT_ID is not set. "
            "Please set NB_QUERY_CLIENT_ID to the client ID for your Neurobagel query tool deployment, to verify the audience claim of ID tokens."
        )


def extract_token(token: str) -> str:
    """
    Extract the token from the authorization header.
    This ensures that it is passed on to downstream APIs without the authorization scheme.
    """
    # Extract the token from the "Bearer" scheme
    # (See https://github.com/tiangolo/fastapi/blob/master/fastapi/security/oauth2.py#L473-L485)
    # TODO: Check also if scheme of token is "Bearer"?
    _, extracted_token = get_authorization_scheme_param(token)
    return extracted_token


def verify_token(token: str) -> str:
    """
    Verify the ID token against the identity provider public keys, and return the token with the authorization scheme stripped.
    Raise an HTTPException if the token is invalid.
    """
    keys_url = "https://neurobagel.ca.auth0.com/.well-known/jwks.json"
    issuer = "https://neurobagel.ca.auth0.com/"

    try:
        extracted_token = extract_token(token)
        # Determine which key was used to sign the token
        # Adapted from https://pyjwt.readthedocs.io/en/stable/usage.html#retrieve-rsa-signing-keys-from-a-jwks-endpoint
        jwks_client = PyJWKClient(keys_url)
        signing_key = jwks_client.get_signing_key_from_jwt(extracted_token)

        # https://pyjwt.readthedocs.io/en/stable/api.html#jwt.decode
        id_info = jwt.decode(
            jwt=extracted_token,
            key=signing_key,
            options={
                "verify_signature": True,
                "require": ["aud", "iss", "exp", "iat"],
            },
            audience=CLIENT_ID,
            issuer=issuer,
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
