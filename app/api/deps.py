"""Shared FastAPI dependencies."""

from __future__ import annotations

from app.services.negotiation_service import NegotiationService

_service: NegotiationService | None = None


def get_negotiation_service() -> NegotiationService:
    """Lazy singleton — instantiated on first request, not at import time."""
    global _service
    if _service is None:
        _service = NegotiationService()
    return _service
