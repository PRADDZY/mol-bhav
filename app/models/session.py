from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.offer import OfferHistory


class NegotiationState(str, Enum):
    IDLE = "idle"
    PROPOSING = "proposing"
    RESPONDING = "responding"
    AGREED = "agreed"
    BROKEN = "broken"
    TIMED_OUT = "timed_out"


class NegotiationSession(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    transaction_id: str = Field(default_factory=lambda: uuid4().hex)
    product_id: str
    product_name: str = ""

    # Negotiation parameters
    anchor_price: float
    reservation_price: float
    beta: float = 5.0  # concession exponent (boulware)
    alpha: float = 0.6  # reciprocity damping
    max_rounds: int = 15
    current_round: int = 0
    ttl_seconds: int = 300

    # State
    state: NegotiationState = NegotiationState.IDLE
    offer_history: OfferHistory = Field(default_factory=OfferHistory)
    current_seller_price: float = 0.0
    agreed_price: float | None = None

    # Security
    bot_score: float = 0.0
    buyer_ip: str = ""

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None

    def is_terminal(self) -> bool:
        return self.state in (
            NegotiationState.AGREED,
            NegotiationState.BROKEN,
            NegotiationState.TIMED_OUT,
        )

    def to_mongo(self) -> dict:
        d = self.model_dump()
        d["_id"] = d.pop("session_id")
        return d

    @classmethod
    def from_mongo(cls, doc: dict) -> "NegotiationSession":
        doc["session_id"] = doc.pop("_id")
        return cls(**doc)
