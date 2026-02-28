"""Authentication dependencies for API routes."""

from __future__ import annotations

from fastapi import Header, HTTPException

from app.config import settings


async def verify_admin_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Validate admin API key for protected routes (product management)."""
    if not settings.api_admin_key:
        # No key configured — allow access (dev mode)
        return "dev"
    if x_api_key != settings.api_admin_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
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
    if not stored_token or x_session_token != stored_token:
        raise HTTPException(status_code=403, detail="Invalid session token")
    return x_session_token
