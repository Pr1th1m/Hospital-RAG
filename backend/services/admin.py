"""
Admin token management – issue, validate, and clean up bearer tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict

from fastapi import Header, HTTPException

from config import ADMIN_TOKEN_TTL_MINUTES

import secrets


# In-memory token store: {token: expiration_utc}
admin_tokens: Dict[str, datetime] = {}


def _issue_admin_token() -> str:
    token = secrets.token_hex(32)
    admin_tokens[token] = datetime.now(timezone.utc) + timedelta(minutes=ADMIN_TOKEN_TTL_MINUTES)
    return token


def _cleanup_expired_tokens() -> None:
    now = datetime.now(timezone.utc)
    expired = [token for token, expires_at in admin_tokens.items() if expires_at <= now]
    for token in expired:
        admin_tokens.pop(token, None)


def verify_admin(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    _cleanup_expired_tokens()
    token = authorization.replace("Bearer ", "", 1).strip()
    expires_at = admin_tokens.get(token)
    if not expires_at:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if expires_at <= datetime.now(timezone.utc):
        admin_tokens.pop(token, None)
        raise HTTPException(status_code=401, detail="Session expired")

    return token
