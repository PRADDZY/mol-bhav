"""Tests for time-dependent concession curve."""

from app.engine.concession import compute_offer, compute_aspiration


def test_round_zero_returns_anchor():
    assert compute_offer(1000, 700, 0, 10, beta=5.0) == 1000


def test_final_round_returns_reservation():
    price = compute_offer(1000, 700, 10, 10, beta=5.0)
    assert price == 700


def test_boulware_holds_firm_mid_negotiation():
    """Beta=5 (boulware) should barely move at round 5/10."""
    price = compute_offer(1000, 700, 5, 10, beta=5.0)
    # Should still be close to anchor — well above 850
    assert price > 850


def test_linear_concedes_proportionally():
    """Beta=1 (linear) at midpoint → midpoint price."""
    price = compute_offer(1000, 700, 5, 10, beta=1.0)
    assert 845 <= price <= 855  # ~850


def test_conceder_drops_fast_early():
    """Beta=0.3 (conceder) moves aggressively early."""
    price = compute_offer(1000, 700, 2, 10, beta=0.3)
    # Should have dropped significantly by round 2
    assert price < 800


def test_clamp_never_below_reservation():
    """Even with extreme parameters, never go below floor."""
    price = compute_offer(1000, 700, 100, 10, beta=0.1)
    assert price >= 700


def test_clamp_never_above_anchor():
    """Never exceed anchor price."""
    price = compute_offer(1000, 700, 0, 10, beta=0.1)
    assert price <= 1000


def test_spot_check_beta3():
    """PRD spot-check: Pa=1000, Rs=700, β=3, t=5, T=10 → ≈762."""
    price = compute_offer(1000, 700, 5, 10, beta=3.0, noise_pct=0.0)
    assert 755 <= price <= 800  # ~762


def test_max_rounds_zero():
    """Edge case: max_rounds=0 → anchor."""
    assert compute_offer(1000, 700, 5, 0, beta=5.0) == 1000


def test_aspiration_starts_at_one():
    assert compute_aspiration(0, 10, beta=5.0) == 1.0


def test_aspiration_ends_at_reserved():
    a = compute_aspiration(10, 10, beta=5.0, reserved_utility=0.0)
    assert abs(a) < 0.01
