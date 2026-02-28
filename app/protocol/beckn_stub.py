"""Stubbed Beckn/ONDC protocol handlers.

Maps Beckn API calls to internal negotiation service.
Real ONDC gateway integration will replace these stubs.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.models.beckn import BecknContext, BecknOnSelectResponse
from app.protocol.quote_builder import build_quote
from app.services.negotiation_service import NegotiationResponse


def build_on_select_response(
    nego_response: NegotiationResponse,
    original_context: BecknContext,
) -> BecknOnSelectResponse:
    """Convert internal negotiation response to Beckn on_select format."""
    quote = build_quote(
        price=nego_response.current_price,
        ttl_seconds=nego_response.quote_ttl_seconds,
    )

    return BecknOnSelectResponse(
        context=BecknContext(
            domain=original_context.domain,
            action="on_select",
            transaction_id=original_context.transaction_id,
            message_id=uuid4().hex,
            timestamp=datetime.utcnow(),
            ttl="PT1M",
        ),
        message={
            "order": {
                "quote": quote.model_dump(),
                "negotiation": {
                    "session_id": nego_response.session_id,
                    "state": nego_response.state,
                    "round": nego_response.round,
                    "seller_message": nego_response.message,
                },
            },
        },
    )
