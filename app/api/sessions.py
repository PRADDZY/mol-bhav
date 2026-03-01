"""Session management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.mongo import sessions_collection, negotiation_logs_collection
from app.auth import verify_session_token

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("/{session_id}")
async def get_session(session_id: str, _token: str = Depends(verify_session_token)):
    """Fetch session details."""
    doc = await sessions_collection().find_one({"_id": session_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    doc["session_id"] = doc.pop("_id")
    return doc


@router.get("/{session_id}/history")
async def get_session_history(
    session_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    _token: str = Depends(verify_session_token),
):
    """Fetch full negotiation log for a session with pagination."""
    cursor = (
        negotiation_logs_collection()
        .find({"session_id": session_id})
        .sort("round", 1)
        .skip(skip)
        .limit(limit)
    )

    logs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        logs.append(doc)

    if not logs:
        raise HTTPException(status_code=404, detail="No history found for this session")
    return logs
