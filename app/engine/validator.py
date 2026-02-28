"""Hallucination guardrail — deterministic price validator.

If the LLM produces a price outside the valid range, this overrides it.
"""

from __future__ import annotations

from pydantic import BaseModel


class ValidatedPrice(BaseModel):
    price: float
    was_overridden: bool = False
    override_reason: str = ""


def validate_price(
    proposed_price: float,
    reservation_price: float,
    anchor_price: float,
) -> ValidatedPrice:
    """Ensure proposed price is within [reservation, anchor].

    - Below floor → reject (override to reservation + small buffer)
    - Above anchor → clamp to anchor
    - Within range → pass through
    """
    if proposed_price < reservation_price:
        return ValidatedPrice(
            price=reservation_price,
            was_overridden=True,
            override_reason=(
                f"LLM proposed {proposed_price} which is below floor "
                f"{reservation_price}. Overridden to floor."
            ),
        )
    if proposed_price > anchor_price:
        return ValidatedPrice(
            price=anchor_price,
            was_overridden=True,
            override_reason=(
                f"LLM proposed {proposed_price} which exceeds anchor "
                f"{anchor_price}. Clamped to anchor."
            ),
        )
    return ValidatedPrice(price=round(proposed_price, 2))
