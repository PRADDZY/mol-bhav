"""Authentication dependencies for API routes."""

from __future__ import annotations

import logging
import secrets

from fastapi import Header, HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


async def verify_admin_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Validate admin API key for protected routes (product management)."""
    if not settings.api_admin_key:
        logger.warning("API_ADMIN_KEY not configured — admin routes are unprotected (dev mode)")
        return "dev"
    if not secrets.compare_digest(x_api_key, settings.api_admin_key):
        raise HTTPException(status_code=403, detail="Forbidden")
    return x_api_key


async def verify_session_token(
    session_id: str,
    x_session_token: str = Header(..., alias="X-Session-Token"),
) -> str:
    """Validate that the caller owns this negotiation session."""
    from app.db import redis as redis_db

    data = await redis_db.load_session(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    stored_token = data.get("session_token", "")
    if not stored_token or not secrets.compare_digest(x_session_token, stored_token):
        raise HTTPException(status_code=403, detail="Forbidden")
    return x_session_token
