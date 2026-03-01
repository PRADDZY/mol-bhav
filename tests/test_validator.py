"""Tests for the hallucination guardrail / price validator."""

import math

import pytest

from app.engine.validator import validate_price


def test_price_in_range_passes():
    v = validate_price(800, 700, 1000)
    assert v.price == 800
    assert not v.was_overridden


def test_price_below_floor_overridden():
    v = validate_price(500, 700, 1000)
    assert v.price == 700
    assert v.was_overridden
    assert "below floor" in v.override_reason


def test_price_above_anchor_clamped():
    v = validate_price(1200, 700, 1000)
    assert v.price == 1000
    assert v.was_overridden
    assert "exceeds anchor" in v.override_reason


def test_exact_floor_passes():
    v = validate_price(700, 700, 1000)
    assert v.price == 700
    assert not v.was_overridden


def test_exact_anchor_passes():
    v = validate_price(1000, 700, 1000)
    assert v.price == 1000
    assert not v.was_overridden


# --- Edge cases added in Phase 4 ---


def test_price_rounds_to_two_decimals():
    v = validate_price(850.456, 700, 1000)
    assert v.price == 850.46
    assert not v.was_overridden


def test_negative_proposed_price_overridden():
    v = validate_price(-100, 700, 1000)
    assert v.price == 700
    assert v.was_overridden


def test_zero_proposed_price_overridden():
    v = validate_price(0, 700, 1000)
    assert v.price == 700
    assert v.was_overridden


def test_nan_proposed_price():
    """NaN < reservation_price is False, so it falls through to the
    anchor check — NaN > anchor_price is also False — so NaN passes
    through unclamped.  validate_price itself doesn't guard against NaN;
    the state machine does.  This test documents current behavior."""
    v = validate_price(float("nan"), 700, 1000)
    assert math.isnan(v.price)


def test_infinity_proposed_price_clamped():
    v = validate_price(float("inf"), 700, 1000)
    assert v.price == 1000
    assert v.was_overridden


def test_negative_infinity_overridden():
    v = validate_price(float("-inf"), 700, 1000)
    assert v.price == 700
    assert v.was_overridden


# --- State machine buyer_price validation ---


class TestBuyerOfferValidation:
    """Tests for process_buyer_offer input validation (Phase 3 fixes)."""

    def _make_engine(self):
        from app.engine.state_machine import NegotiationEngine
        from app.models.session import NegotiationSession

        session = NegotiationSession(
            product_id="test-prod",
            product_name="Test Widget",
            anchor_price=1000,
            reservation_price=700,
        )
        return NegotiationEngine(session)

    def test_nan_buyer_price_raises(self):
        engine = self._make_engine()
        with pytest.raises(ValueError, match="finite number"):
            engine.process_buyer_offer(float("nan"))

    def test_inf_buyer_price_raises(self):
        engine = self._make_engine()
        with pytest.raises(ValueError, match="finite number"):
            engine.process_buyer_offer(float("inf"))

    def test_negative_inf_buyer_price_raises(self):
        engine = self._make_engine()
        with pytest.raises(ValueError, match="finite number"):
            engine.process_buyer_offer(float("-inf"))

    def test_zero_buyer_price_raises(self):
        engine = self._make_engine()
        with pytest.raises(ValueError, match="positive"):
            engine.process_buyer_offer(0)

    def test_negative_buyer_price_raises(self):
        engine = self._make_engine()
        with pytest.raises(ValueError, match="positive"):
            engine.process_buyer_offer(-500)
