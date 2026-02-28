"""Invisible coupon service (Feature F-03).

Checks backend promotions and applies discounts transparently.
The AI frames them as personal favours — never reveals coupon codes.
"""

from __future__ import annotations

import logging
from datetime import datetime

from pydantic import BaseModel

from app.db.mongo import promotions_collection

logger = logging.getLogger(__name__)


class AppliedCoupon(BaseModel):
    promo_id: str
    discount_amount: float
    description: str  # internal, not shown to buyer


async def find_applicable(product_id: str, current_price: float) -> AppliedCoupon | None:
    """Check if any active promotion applies to this product.

    Returns the best (highest discount) applicable promotion, or None.
    """
    coll = promotions_collection()
    now = datetime.utcnow()

    cursor = coll.find({
        "$or": [
            {"product_id": product_id},
            {"product_id": "__all__"},  # store-wide promos
        ],
        "active": True,
        "valid_from": {"$lte": now},
        "valid_until": {"$gte": now},
    })

    best: AppliedCoupon | None = None

    async for doc in cursor:
        discount_type = doc.get("discount_type", "flat")
        discount_value = doc.get("discount_value", 0)

        if discount_type == "percentage":
            amount = current_price * (discount_value / 100)
        else:
            amount = discount_value

        min_price = doc.get("min_price", 0)
        if current_price < min_price:
            continue

        if best is None or amount > best.discount_amount:
            best = AppliedCoupon(
                promo_id=str(doc.get("_id", "")),
                discount_amount=round(amount, 2),
                description=doc.get("description", "Promotional discount"),
            )

    if best:
        logger.info("Applied invisible coupon %s: -₹%.2f", best.promo_id, best.discount_amount)

    return best
