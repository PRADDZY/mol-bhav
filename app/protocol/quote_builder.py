"""Beckn quote builder — constructs ONDC-compliant quote objects."""

from __future__ import annotations

from app.models.beckn import BecknBreakupItem, BecknPrice, BecknQuote


def seconds_to_iso_duration(seconds: int) -> str:
    """Convert seconds to ISO 8601 duration string.

    300 → "PT5M", 3600 → "PT1H", 90 → "PT1M30S"
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = ["PT"]
    if hours:
        parts.append(f"{hours}H")
    if minutes:
        parts.append(f"{minutes}M")
    if secs:
        parts.append(f"{secs}S")
    if len(parts) == 1:
        parts.append("0S")
    return "".join(parts)


def build_quote(
    price: float,
    ttl_seconds: int = 300,
    delivery_charge: float = 0.0,
    discount: float = 0.0,
) -> BecknQuote:
    """Build a Beckn-compliant quote object with breakup and TTL."""
    breakup = [
        BecknBreakupItem(
            title="Item Price",
            price=BecknPrice(value=str(price)),
        ),
    ]

    if delivery_charge > 0:
        breakup.append(
            BecknBreakupItem(
                title="Delivery Charge",
                price=BecknPrice(value=str(delivery_charge)),
            )
        )

    if discount > 0:
        breakup.append(
            BecknBreakupItem(
                title="Discount",
                price=BecknPrice(value=str(-discount)),
            )
        )

    total = price + delivery_charge - discount

    return BecknQuote(
        price=BecknPrice(value=str(round(total, 2))),
        breakup=breakup,
        ttl=seconds_to_iso_duration(ttl_seconds),
    )
