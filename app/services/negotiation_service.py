"""Central negotiation orchestrator.

Binds together:
  - Bot detector (security)
  - Sentiment analysis (exit intent)
  - SAO engine (strategy)
  - Dialogue generator (Hinglish responses)
  - Price validator (guardrail)
  - Coupon service (invisible discounts)
  - Database persistence (Mongo + Redis)
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel

from app.config import settings
from app.db import mongo, redis
from app.dialogue.generator import DialogueGenerator, DialogueResponse
from app.dialogue.sentiment import detect_exit_intent
from app.engine.bot_detector import BotDetector
from app.engine.state_machine import EngineResult, NegotiationEngine
from app.engine.validator import validate_price
from app.models.product import Product
from app.models.session import NegotiationSession, NegotiationState
from app.services import coupon_service

logger = logging.getLogger(__name__)


class NegotiationResponse(BaseModel):
    session_id: str
    session_token: str = ""
    message: str
    current_price: float
    state: str
    tactic: str
    sentiment: str
    round: int
    max_rounds: int
    quote_ttl_seconds: int
    agreed_price: float | None = None
    metadata: dict = {}


class NegotiationService:
    def __init__(self):
        self._dialogue = DialogueGenerator()
        self._bot_detectors: dict[str, BotDetector] = {}

    async def start(
        self,
        product_id: str,
        buyer_name: str = "",
        buyer_ip: str = "",
    ) -> NegotiationResponse:
        """Start a new negotiation session for a product."""
        # Fetch product from DB
        doc = await mongo.products_collection().find_one({"_id": product_id})
        if not doc:
            raise ValueError(f"Product {product_id} not found")

        doc["id"] = doc.pop("_id")
        product = Product(**doc)

        # Create session
        session = NegotiationSession(
            product_id=product_id,
            product_name=product.name,
            anchor_price=product.anchor_price,
            reservation_price=product.reservation_price,
            beta=settings.default_beta,
            alpha=settings.default_alpha,
            max_rounds=settings.default_max_rounds,
            ttl_seconds=settings.default_session_ttl_seconds,
            buyer_ip=buyer_ip,
            session_token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.default_session_ttl_seconds),
        )

        # Start engine
        engine = NegotiationEngine(session)
        result = engine.start_negotiation()

        # Generate opening dialogue
        dialogue = await self._dialogue.generate_response(
            session, result, buyer_name or "Customer"
        )

        # Persist
        await self._persist_session(session)

        return self._build_response(session, dialogue, result)

    async def negotiate(
        self,
        session_id: str,
        buyer_message: str,
        buyer_price: float,
    ) -> NegotiationResponse:
        """Process one round of negotiation."""        # Acquire per-session lock to prevent concurrent modifications
        if not await redis.acquire_session_lock(session_id):
            raise ValueError(f"Session {session_id} is currently being processed, try again")

        try:
            return await self._negotiate_locked(session_id, buyer_message, buyer_price)
        finally:
            await redis.release_session_lock(session_id)

    async def _negotiate_locked(
        self,
        session_id: str,
        buyer_message: str,
        buyer_price: float,
    ) -> NegotiationResponse:
        \"\"\"Internal negotiate logic, called under session lock.\"\"\"        # Load session
        session = await self.load_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found or expired")

        if session.is_terminal():
            raise ValueError(f"Session {session_id} is already {session.state.value}")

        # --- Bot detection ---
        detector = self._get_bot_detector(session_id)
        detector.record(datetime.now(timezone.utc), buyer_price)
        bot_score = detector.compute_bot_score()
        session.bot_score = bot_score

        # Adjust strategy if suspicious
        effective_beta = BotDetector.recommended_beta(bot_score, session.beta)

        # --- Exit intent detection ---
        exit_intent = detect_exit_intent(buyer_message)

        # --- Engine processing ---
        engine = NegotiationEngine(session)

        if exit_intent.is_leaving and exit_intent.confidence >= 0.5:
            result = engine.handle_walk_away()
        else:
            # Temporarily adjust beta for this round if bot suspected
            original_beta = session.beta
            session.beta = effective_beta
            result = engine.process_buyer_offer(buyer_price)
            session.beta = original_beta  # restore for storage

        # --- Invisible coupons (F-03) ---
        if result.state == NegotiationState.RESPONDING:
            coupon = await coupon_service.find_applicable(
                session.product_id, result.counter_price
            )
            if coupon:
                new_price = result.counter_price - coupon.discount_amount
                validated = validate_price(
                    new_price, session.reservation_price, session.anchor_price
                )
                if not validated.was_overridden:
                    result.counter_price = validated.price
                    result.metadata["coupon_applied"] = True
                    result.metadata["coupon_discount"] = coupon.discount_amount

        # --- Dialogue generation ---
        dialogue = await self._dialogue.generate_response(session, result, buyer_message)

        # --- Persist ---
        await self._persist_session(session)

        # Cleanup bot detector if session reached terminal state
        if session.is_terminal():
            self._bot_detectors.pop(session_id, None)

        # --- Log negotiation turn ---
        await mongo.negotiation_logs_collection().insert_one({
            "session_id": session_id,
            "round": session.current_round,
            "buyer_message": buyer_message[:500],  # truncate for PII safety
            "buyer_price": buyer_price,
            "counter_price": result.counter_price,
            "tactic": result.tactic,
            "bot_score": bot_score,
            "state": result.state.value,
            "timestamp": datetime.now(timezone.utc),
        })

        return self._build_response(session, dialogue, result)

    # --- Private helpers ---

    def _get_bot_detector(self, session_id: str) -> BotDetector:
        if session_id not in self._bot_detectors:
            # Prune stale detectors to prevent unbounded growth
            if len(self._bot_detectors) > 1000:
                oldest_keys = list(self._bot_detectors.keys())[:500]
                for k in oldest_keys:
                    del self._bot_detectors[k]
            self._bot_detectors[session_id] = BotDetector()
        return self._bot_detectors[session_id]

    async def _persist_session(self, session: NegotiationSession) -> None:
        # Redis (active state with TTL)
        await redis.store_session(
            session.session_id,
            session.model_dump(),
            session.ttl_seconds,
        )
        # Mongo (durable history)
        await mongo.sessions_collection().replace_one(
            {"_id": session.session_id},
            session.to_mongo(),
            upsert=True,
        )

    async def load_session(self, session_id: str) -> NegotiationSession | None:
        # Try Redis first (fast, includes TTL check)
        data = await redis.load_session(session_id)
        if data:
            return NegotiationSession(**data)

        # Fallback to Mongo
        doc = await mongo.sessions_collection().find_one({"_id": session_id})
        if doc:
            return NegotiationSession.from_mongo(doc)

        return None

    def _build_response(
        self,
        session: NegotiationSession,
        dialogue: DialogueResponse,
        result: EngineResult,
    ) -> NegotiationResponse:
        return NegotiationResponse(
            session_id=session.session_id,
            session_token=session.session_token,
            message=dialogue.message,
            current_price=result.counter_price,
            state=result.state.value,
            tactic=dialogue.tactic,
            sentiment=dialogue.sentiment,
            round=session.current_round,
            max_rounds=session.max_rounds,
            quote_ttl_seconds=session.ttl_seconds,
            agreed_price=session.agreed_price,
            metadata=result.metadata,
        )
