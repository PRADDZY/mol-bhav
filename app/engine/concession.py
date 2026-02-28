"""Time-dependent concession curve.

P(t) = Pa + (Rs - Pa) * (t / T) ^ beta

Where:
  Pa   = anchor price (starting list price)
  Rs   = reservation price (floor / walk-away)
  t    = current round
  T    = max rounds (deadline)
  beta = concession exponent
         beta >> 1  → Boulware (hardliner, concedes late)
         beta == 1  → Linear
         beta < 1   → Conceder (gives in early)
"""

import random


def compute_offer(
    anchor: float,
    reservation: float,
    current_round: int,
    max_rounds: int,
    beta: float = 5.0,
    noise_pct: float = 0.0,
) -> float:
    """Compute the seller's offer price at round `current_round`.

    Args:
        anchor: Starting (list) price.
        reservation: Absolute floor price — never go below.
        current_round: Current negotiation round (0-indexed, round 0 = anchor).
        max_rounds: Total allowed rounds (deadline T).
        beta: Concession exponent.  >1 = boulware, 1 = linear, <1 = conceder.
        noise_pct: Random jitter as fraction of (anchor - reservation), e.g. 0.02.
                   Prevents pattern detection by sophisticated buyers.

    Returns:
        Offer price, clamped within [reservation, anchor].
    """
    if max_rounds <= 0:
        return anchor
    if current_round <= 0:
        return anchor

    t = min(current_round, max_rounds)
    ratio = t / max_rounds  # 0 → 1

    # F(t) = (t/T) ^ beta   (beta>1 = boulware, beta<1 = conceder)
    f_t = ratio ** beta

    # P(t) = Pa + (Rs - Pa) * F(t)
    price = anchor + (reservation - anchor) * f_t

    # Optional noise
    if noise_pct > 0:
        spread = abs(anchor - reservation) * noise_pct
        price += random.uniform(-spread, spread)

    # Clamp
    return round(max(reservation, min(anchor, price)), 2)


def compute_aspiration(
    current_round: int,
    max_rounds: int,
    beta: float = 5.0,
    reserved_utility: float = 0.0,
) -> float:
    """Compute aspiration level in utility space [0, 1].

    a(t) = 1 - (1 - r) * (t/T)^(1/beta)
    """
    if max_rounds <= 0 or current_round <= 0:
        return 1.0
    t = min(current_round, max_rounds)
    ratio = t / max_rounds
    return 1.0 - (1.0 - reserved_utility) * (ratio ** beta)
