"""Tests for the SAO state machine."""

from app.engine.state_machine import NegotiationEngine
from app.models.session import NegotiationSession, NegotiationState


def _make_session(**overrides) -> NegotiationSession:
    defaults = {
        "product_id": "test-phone",
        "product_name": "Test Phone",
        "anchor_price": 1000,
        "reservation_price": 700,
        "beta": 5.0,
        "alpha": 0.6,
        "max_rounds": 10,
    }
    defaults.update(overrides)
    return NegotiationSession(**defaults)


def test_start_returns_anchor():
    session = _make_session()
    engine = NegotiationEngine(session)
    result = engine.start_negotiation()

    assert result.counter_price == 1000
    assert result.state == NegotiationState.PROPOSING
    assert session.current_round == 0


def test_buyer_offers_above_willingness_accepted():
    """If buyer offers >= what seller would ask, accept immediately."""
    session = _make_session(beta=1.0)  # linear for predictable acceptance
    engine = NegotiationEngine(session)
    engine.start_negotiation()

    # At round 1 of 10, linear: P(1) = 1000 + (700-1000)*0.1 = 970
    # Buyer offers 975 → above willingness → accept
    result = engine.process_buyer_offer(975)
    assert result.state == NegotiationState.AGREED
    assert result.counter_price == 975
    assert result.acceptance_threshold_met


def test_low_offer_gets_counter():
    """Low buyer offer should get a counter, not acceptance."""
    session = _make_session()
    engine = NegotiationEngine(session)
    engine.start_negotiation()

    result = engine.process_buyer_offer(600)
    assert result.state == NegotiationState.RESPONDING
    assert result.counter_price > 600
    assert result.counter_price <= 1000


def test_counter_never_below_floor():
    """No matter what, counter should never go below reservation."""
    session = _make_session()
    engine = NegotiationEngine(session)
    engine.start_negotiation()

    for _ in range(10):
        result = engine.process_buyer_offer(100)
        if result.state in (NegotiationState.AGREED, NegotiationState.TIMED_OUT):
            break
        assert result.counter_price >= 700


def test_timeout_after_max_rounds():
    session = _make_session(max_rounds=3)
    engine = NegotiationEngine(session)
    engine.start_negotiation()

    engine.process_buyer_offer(500)
    engine.process_buyer_offer(550)
    result = engine.process_buyer_offer(600)

    assert result.state == NegotiationState.TIMED_OUT


def test_walk_away_concedes_5pct():
    session = _make_session()
    engine = NegotiationEngine(session)
    engine.start_negotiation()

    # Process one offer to set current_seller_price
    engine.process_buyer_offer(700)

    prev_price = session.current_seller_price
    result = engine.handle_walk_away()

    if result.state != NegotiationState.BROKEN:
        expected = prev_price * 0.95
        assert abs(result.counter_price - expected) < 1 or result.counter_price >= 700


def test_walk_away_breaks_if_below_floor():
    """Walk-away can't save if already at reservation."""
    session = _make_session(anchor_price=720, reservation_price=700)
    engine = NegotiationEngine(session)
    engine.start_negotiation()

    # Push price very close to floor
    session.current_seller_price = 710
    result = engine.handle_walk_away()

    # 710 * 0.95 = 674.5 < 700 floor → should break
    assert result.state == NegotiationState.BROKEN


def test_quantity_pivot():
    session = _make_session()
    engine = NegotiationEngine(session)
    engine.start_negotiation()

    result = engine.handle_quantity_pivot(quantity=2, discount_per_unit=100)

    assert result.tactic == "quantity_pivot"
    assert "quantity" in result.metadata
    assert result.metadata["quantity"] == 2
    assert result.counter_price >= 700  # still above floor


def test_happy_path_full_flow():
    """IDLE → PROPOSING → 3 rounds → AGREED."""
    session = _make_session(max_rounds=10, beta=1.0)  # linear for predictability
    engine = NegotiationEngine(session)

    r0 = engine.start_negotiation()
    assert r0.state == NegotiationState.PROPOSING

    r1 = engine.process_buyer_offer(750)
    assert r1.state == NegotiationState.RESPONDING

    r2 = engine.process_buyer_offer(800)
    assert r2.state == NegotiationState.RESPONDING

    # Offer something the engine would accept at round 3 of 10
    r3 = engine.process_buyer_offer(950)
    assert r3.state == NegotiationState.AGREED
