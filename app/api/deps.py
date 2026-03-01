"""Shared FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache

from app.services.negotiation_service import NegotiationService


@lru_cache(maxsize=1)
def get_negotiation_service() -> NegotiationService:
    """Lazy singleton — instantiated on first request, not at import time."""
    return NegotiationService()
