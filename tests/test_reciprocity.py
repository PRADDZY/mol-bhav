"""Tests for Tit-for-Tat reciprocity tracker."""

from app.engine.reciprocity import ReciprocityTracker


def test_no_offers_zero_concession():
    t = ReciprocityTracker(alpha=0.6)
    assert t.compute_ai_concession() == 0.0


def test_buyer_concedes_50_ai_concedes_30():
    """PRD spec: buyer ₹50 → AI ₹30 at alpha=0.6."""
    t = ReciprocityTracker(alpha=0.6)
    t.record_buyer_offer(500)
    t.record_buyer_offer(550)  # conceded +50
    ai = t.compute_ai_concession()
    assert abs(ai - 30.0) < 0.1


def test_buyer_holds_firm_ai_holds():
    """If buyer doesn't concede, AI holds firm."""
    t = ReciprocityTracker(alpha=0.6)
    t.record_buyer_offer(500)
    t.record_buyer_offer(500)  # no movement
    assert t.compute_ai_concession() == 0.0


def test_buyer_retreats_ai_holds():
    """If buyer lowers their offer, AI doesn't concede."""
    t = ReciprocityTracker(alpha=0.6)
    t.record_buyer_offer(500)
    t.record_buyer_offer(480)  # negative delta
    assert t.compute_ai_concession() == 0.0


def test_max_concession_cap():
    """AI concession should never exceed max_concession."""
    t = ReciprocityTracker(alpha=0.6, max_concession=20.0)
    t.record_buyer_offer(500)
    t.record_buyer_offer(600)  # conceded +100, AI would want 60 but cap is 20
    assert t.compute_ai_concession() == 20.0


def test_sliding_window():
    """Tracker uses last N offers for averaging."""
    t = ReciprocityTracker(alpha=0.6, window=2)
    t.record_buyer_offer(500)
    t.record_buyer_offer(530)  # +30
    t.record_buyer_offer(550)  # +20
    t.record_buyer_offer(560)  # +10
    # Window of 2: last deltas are [+20, +10], avg = 15
    ai = t.compute_ai_concession()
    assert abs(ai - 9.0) < 0.1  # 0.6 * 15 = 9


def test_detect_trend_stable():
    t = ReciprocityTracker()
    t.record_buyer_offer(500)
    t.record_buyer_offer(520)  # +20
    t.record_buyer_offer(540)  # +20
    assert t.detect_trend() == "stable"


def test_detect_trend_decelerating():
    t = ReciprocityTracker()
    t.record_buyer_offer(500)
    t.record_buyer_offer(550)  # +50
    t.record_buyer_offer(560)  # +10
    t.record_buyer_offer(562)  # +2
    assert t.detect_trend() == "decelerating"


def test_detect_trend_stalled():
    t = ReciprocityTracker()
    t.record_buyer_offer(500)
    t.record_buyer_offer(500)
    t.record_buyer_offer(500)
    t.record_buyer_offer(500)
    assert t.detect_trend() == "stalled"


def test_adaptive_alpha_early():
    """Early in negotiation, alpha stays at base."""
    t = ReciprocityTracker(alpha=0.6)
    assert t.adaptive_alpha(0.1) == 0.6  # relative_time < 0.5 → no boost


def test_adaptive_alpha_late():
    """Near deadline, alpha increases toward 1.0."""
    t = ReciprocityTracker(alpha=0.6)
    a = t.adaptive_alpha(1.0)  # at deadline
    assert a == 1.0
