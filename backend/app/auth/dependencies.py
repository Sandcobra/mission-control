from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import settings

_http_basic = HTTPBasic(auto_error=False)


async def verify_agent_api_key(request: Request) -> str:
    """
    Validate the X-MC-API-Key header against the configured list of agent keys.

    Returns the validated key on success; raises HTTP 403 on failure.
    """
    api_key = request.headers.get(settings.api_key_header)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing API key header.",
        )

    valid_keys = settings.agent_keys_list
    # Use constant-time comparison for every key to prevent timing attacks.
    matched = any(secrets.compare_digest(api_key, valid_key) for valid_key in valid_keys)
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )
    return api_key


async def verify_operator(
    credentials: HTTPBasicCredentials = Depends(_http_basic),
) -> bool:
    """
    HTTP Basic Auth check for operator (dashboard / admin) endpoints.

    Returns True on success; raises HTTP 401 on failure.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operator credentials required.",
            headers={"WWW-Authenticate": "Basic"},
        )

    correct_username = secrets.compare_digest(
        credentials.username, settings.operator_username
    )
    correct_password = secrets.compare_digest(
        credentials.password, settings.operator_password
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid operator credentials.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True
