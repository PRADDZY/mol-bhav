"""Beckn protocol API routes (stubbed).

Exposes /beckn/select endpoint that maps ONDC protocol to our
internal negotiation engine.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.models.beckn import BecknContext, BecknSelectRequest
from app.protocol.beckn_stub import build_on_select_response
from app.api.deps import get_negotiation_service
from app.services.negotiation_service import NegotiationService

router = APIRouter(prefix="/beckn", tags=["beckn"])


@router.post("/select")
async def beckn_select(
    body: BecknSelectRequest,
    service: NegotiationService = Depends(get_negotiation_service),
):
    """Handle Beckn /select — buyer indicates interest with optional price signal.

    Maps to internal negotiation and returns on_select with quote + TTL.
    """
    msg = body.message
    order = msg.get("order", {})
    items = order.get("items", [])

    if not items:
        raise HTTPException(status_code=400, detail="No items in select message")

    item = items[0]
    product_id = item.get("id", "")
    try:
        buyer_price = float(item.get("price", {}).get("value", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid price value")

    # Check if this is a new negotiation or continuation
    session_id = order.get("negotiation", {}).get("session_id")

    if session_id:
        # Continuation — process as offer
        buyer_msg = item.get("tags", {}).get("message", "")
        try:
            result = await service.negotiate(
                session_id=session_id,
                buyer_message=buyer_msg,
                buyer_price=buyer_price,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # New negotiation — start session
        try:
            result = await service.start(product_id=product_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    response = build_on_select_response(result, body.context)
    return response.model_dump()
