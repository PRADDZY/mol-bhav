"""SAO (Stacked Alternating Offers) state machine.

States:  IDLE → PROPOSING → RESPONDING → { AGREED | BROKEN | TIMED_OUT }

This orchestrates the concession curve + TFT reciprocity into a unified
negotiation strategy engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.engine.concession import compute_offer
from app.engine.reciprocity import ReciprocityTracker
from app.engine.validator import ValidatedPrice, validate_price
from app.models.offer import Actor, Offer
from app.models.session import NegotiationSession, NegotiationState


@dataclass
class EngineResult:
    """Output of a single negotiation turn."""

    counter_price: float
    state: NegotiationState
    tactic: str = ""  # e.g. "concession", "hold_firm", "walk_away_save", "quantity_pivot"
    acceptance_threshold_met: bool = False
    validation: ValidatedPrice | None = None
    metadata: dict = field(default_factory=dict)


class NegotiationEngine:
    """Core SAO negotiation engine."""

    def __init__(self, session: NegotiationSession):
        self.session = session
        self.tracker = ReciprocityTracker(
            alpha=session.alpha,
            max_concession=abs(session.anchor_price - session.reservation_price) * 0.1,
        )
        # Replay buyer history into tracker
        for offer in session.offer_history.buyer_offers:
            self.tracker.record_buyer_offer(offer.price)

    def start_negotiation(self) -> EngineResult:
        """Begin negotiation — seller opens with anchor price."""
        self.session.state = NegotiationState.PROPOSING
        self.session.current_round = 0
        self.session.current_seller_price = self.session.anchor_price
        self.session.updated_at = datetime.now(timezone.utc)

        offer = Offer(
            round=0,
            actor=Actor.SELLER,
            price=self.session.anchor_price,
            message="Opening offer",
        )
        self.session.offer_history.add(offer)

        return EngineResult(
            counter_price=self.session.anchor_price,
            state=NegotiationState.PROPOSING,
            tactic="opening",
        )

    def process_buyer_offer(self, buyer_price: float) -> EngineResult:
        """Process incoming buyer offer and generate counter."""
        import math
        if not isinstance(buyer_price, (int, float)) or math.isnan(buyer_price) or math.isinf(buyer_price):
            raise ValueError("buyer_price must be a finite number")
        if buyer_price <= 0:
            raise ValueError("buyer_price must be positive")

        s = self.session
        s.current_round += 1
        s.state = NegotiationState.RESPONDING
        s.updated_at = datetime.now(timezone.utc)

        # Record buyer offer
        buyer_offer = Offer(
            round=s.current_round,
            actor=Actor.BUYER,
            price=buyer_price,
        )
        if s.offer_history.buyer_offers:
            prev = s.offer_history.buyer_offers[-1].price
            buyer_offer.concession_delta = buyer_price - prev
        s.offer_history.add(buyer_offer)
        self.tracker.record_buyer_offer(buyer_price)

        # --- Check acceptance ---
        # If buyer offers at or above our current willingness, accept
        base_price = compute_offer(
            anchor=s.anchor_price,
            reservation=s.reservation_price,
            current_round=s.current_round,
            max_rounds=s.max_rounds,
            beta=s.beta,
        )
        if buyer_price >= base_price:
            return self._accept(buyer_price)

        # --- Check timeout ---
        if s.current_round >= s.max_rounds:
            return self._timeout()

        # --- Compute counter-offer ---
        counter = self._compute_counter(base_price)

        # Record seller counter
        seller_offer = Offer(
            round=s.current_round,
            actor=Actor.SELLER,
            price=counter.price,
            concession_delta=(s.current_seller_price - counter.price),
            message="counter",
        )
        s.offer_history.add(seller_offer)
        s.current_seller_price = counter.price

        # Determine tactic for dialogue engine
        tactic = self._classify_tactic(counter.price, base_price)

        return EngineResult(
            counter_price=counter.price,
            state=NegotiationState.RESPONDING,
            tactic=tactic,
            validation=counter,
        )

    def handle_walk_away(self) -> EngineResult:
        """Buyer signalled exit intent — "Digital Flounce" save-the-deal.

        Concede 5% if within ZOPA, otherwise let them go.
        """
        s = self.session
        current = s.current_seller_price or s.anchor_price
        concession = current * 0.05
        new_price = current - concession

        if new_price < s.reservation_price:
            # Can't save the deal — below floor
            s.state = NegotiationState.BROKEN
            s.updated_at = datetime.now(timezone.utc)
            return EngineResult(
                counter_price=s.reservation_price,
                state=NegotiationState.BROKEN,
                tactic="walk_away_failed",
            )

        validated = validate_price(new_price, s.reservation_price, s.anchor_price)

        offer = Offer(
            round=s.current_round,
            actor=Actor.SELLER,
            price=validated.price,
            concession_delta=current - validated.price,
            message="walk_away_save",
        )
        s.offer_history.add(offer)
        s.current_seller_price = validated.price
        s.updated_at = datetime.now(timezone.utc)

        return EngineResult(
            counter_price=validated.price,
            state=NegotiationState.RESPONDING,
            tactic="walk_away_save",
            validation=validated,
        )

    def handle_quantity_pivot(self, quantity: int, discount_per_unit: float = 100.0) -> EngineResult:
        """Price negotiation stuck → pivot to quantity bargaining (F-04).

        'I can't drop the price for 1, but take 2 and I'll give you ₹X off.'
        """
        s = self.session
        if quantity < 2:
            quantity = 2

        unit_price = s.current_seller_price or s.anchor_price
        total_discount = discount_per_unit * (quantity - 1)
        bundle_unit_price = unit_price - (total_discount / quantity)

        validated = validate_price(bundle_unit_price, s.reservation_price, s.anchor_price)

        return EngineResult(
            counter_price=validated.price,
            state=s.state,
            tactic="quantity_pivot",
            validation=validated,
            metadata={"quantity": quantity, "bundle_total": round(validated.price * quantity, 2)},
        )

    # --- Private helpers ---

    def _compute_counter(self, base_price: float) -> ValidatedPrice:
        """Hybrid counter: time-curve base + TFT perturbation."""
        tft_concession = self.tracker.compute_ai_concession()

        # Blend: use the lower of base_price or (current - tft_concession)
        current = self.session.current_seller_price or self.session.anchor_price
        tft_price = current - tft_concession

        # Take the more generous of the two (lower price)
        counter = min(current, max(base_price, tft_price))

        return validate_price(counter, self.session.reservation_price, self.session.anchor_price)

    def _accept(self, agreed_price: float) -> EngineResult:
        s = self.session
        s.state = NegotiationState.AGREED
        s.agreed_price = agreed_price
        s.updated_at = datetime.now(timezone.utc)
        return EngineResult(
            counter_price=agreed_price,
            state=NegotiationState.AGREED,
            tactic="accept",
            acceptance_threshold_met=True,
        )

    def _timeout(self) -> EngineResult:
        s = self.session
        # Last-ditch: offer reservation price
        s.state = NegotiationState.TIMED_OUT
        s.updated_at = datetime.now(timezone.utc)
        return EngineResult(
            counter_price=s.reservation_price,
            state=NegotiationState.TIMED_OUT,
            tactic="timeout_final",
        )

    def _classify_tactic(self, counter_price: float, base_price: float) -> str:
        s = self.session
        current = s.current_seller_price or s.anchor_price
        drop = current - counter_price
        total_range = s.anchor_price - s.reservation_price

        if total_range == 0:
            return "hold_firm"

        drop_pct = drop / total_range
        if drop_pct < 0.01:
            return "hold_firm"
        elif drop_pct < 0.05:
            return "minor_concession"
        elif drop_pct < 0.15:
            return "concession"
        else:
            return "major_concession"
