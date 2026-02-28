"""Tests for bot detection heuristics."""

from datetime import datetime, timedelta

from app.engine.bot_detector import BotDetector


def test_insufficient_data_returns_zero():
    d = BotDetector()
    d.record(datetime.now(), 500)
    d.record(datetime.now(), 520)
    assert d.compute_bot_score() == 0.0


def test_rapid_fire_high_timing_score():
    """Messages < 1 second apart → high timing score."""
    d = BotDetector()
    base = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(5):
        d.record(base + timedelta(milliseconds=300 * i), 500 + i * 10)
    assert d.score_timing() > 0.5


def test_natural_timing_low_score():
    """Messages 5-15 seconds apart → low timing score."""
    d = BotDetector()
    base = datetime(2026, 1, 1, 12, 0, 0)
    intervals = [0, 7, 12, 20, 28]  # seconds, varying
    for t in intervals:
        d.record(base + timedelta(seconds=t), 500 + t * 5)
    assert d.score_timing() < 0.3


def test_fixed_increment_high_pattern_score():
    """Offers go up by exactly ₹50 each time → suspicious pattern."""
    d = BotDetector()
    base = datetime(2026, 1, 1)
    for i in range(6):
        d.record(base + timedelta(seconds=i * 10), 500 + i * 50)
    assert d.score_pattern() == 1.0


def test_varied_offers_low_pattern_score():
    """Non-algorithmic offer pattern → low score."""
    d = BotDetector()
    base = datetime(2026, 1, 1)
    offers = [500, 530, 545, 560, 590, 600]
    for i, price in enumerate(offers):
        d.record(base + timedelta(seconds=i * 10), price)
    assert d.score_pattern() < 0.5


def test_recommended_beta_normal():
    assert BotDetector.recommended_beta(0.1, 5.0) == 5.0


def test_recommended_beta_suspicious():
    assert BotDetector.recommended_beta(0.5, 5.0) == 10.0


def test_recommended_beta_bot():
    assert BotDetector.recommended_beta(0.8, 5.0) == 20.0
