"""Negotiation API routes — the main interaction endpoints."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.db.redis import check_cooldown, set_cooldown, get_redis
from app.config import settings
from app.api.deps import get_negotiation_service
from app.auth import verify_session_token
from app.services.negotiation_service import NegotiationService

router = APIRouter(prefix="/api/v1/negotiate", tags=["negotiate"])

_SESSION_ID_RE = re.compile(r"^[a-f0-9]{32}$")


async def _check_ip_rate_limit(ip: str) -> None:
    """Enforce per-IP rate limiting on /start using Redis."""
    r = get_redis()
    key = f"nego:ratelimit:{ip}"
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, 60)
    if count > settings.max_requests_per_minute_per_ip:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")


class StartRequest(BaseModel):
    product_id: str
    buyer_name: str = ""


class OfferRequest(BaseModel):
    message: str = ""
    price: float = Field(gt=0)


@router.post("/start")
async def start_negotiation(
    body: StartRequest,
    request: Request,
    service: NegotiationService = Depends(get_negotiation_service),
):
    """Begin a new negotiation session for a product."""
    try:
        buyer_ip = request.client.host if request.client else ""
        if buyer_ip:
            await _check_ip_rate_limit(buyer_ip)
        result = await service.start(
            product_id=body.product_id,
            buyer_name=body.buyer_name,
            buyer_ip=buyer_ip,
        )
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{session_id}/offer")
async def make_offer(
    session_id: str,
    body: OfferRequest,
    _token: str = Depends(verify_session_token),
    service: NegotiationService = Depends(get_negotiation_service),
):
    """Submit a buyer offer in an active negotiation."""
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # Cooldown check (bot defense — 2s between turns)
    if await check_cooldown(session_id):
        raise HTTPException(
            status_code=429,
            detail="Please wait before making another offer.",
        )

    try:
        result = await service.negotiate(
            session_id=session_id,
            buyer_message=body.message,
            buyer_price=body.price,
        )
        # Set cooldown after successful processing
        await set_cooldown(session_id, settings.min_response_delay_ms)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/status")
async def get_status(
    session_id: str,
    _token: str = Depends(verify_session_token),
    service: NegotiationService = Depends(get_negotiation_service),
):
    """Get current negotiation status."""
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    session = await service.load_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return {
        "session_id": session.session_id,
        "state": session.state.value,
        "current_round": session.current_round,
        "max_rounds": session.max_rounds,
        "current_seller_price": session.current_seller_price,
        "agreed_price": session.agreed_price,
        "bot_score": session.bot_score,
    }
