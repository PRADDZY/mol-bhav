"""Tests for the hallucination guardrail / price validator."""

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
