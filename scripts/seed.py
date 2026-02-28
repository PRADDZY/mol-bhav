"""Seed script — inserts demo products and promotions (idempotent upserts)."""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

PRODUCTS = [
    {
        "_id": "iphone-15",
        "name": "iPhone 15 (128 GB)",
        "category": "electronics",
        "anchor_price": 79900,
        "cost_price": 65000,
        "min_margin": 0.05,
        "target_margin": 0.15,
        "metadata": {"brand": "Apple", "color": "Black"},
    },
    {
        "_id": "nike-air-max",
        "name": "Nike Air Max 270",
        "category": "footwear",
        "anchor_price": 12995,
        "cost_price": 7000,
        "min_margin": 0.10,
        "target_margin": 0.30,
        "metadata": {"brand": "Nike", "size": "UK 9"},
    },
    {
        "_id": "samsung-tv-55",
        "name": "Samsung Crystal 4K 55\" Smart TV",
        "category": "electronics",
        "anchor_price": 54990,
        "cost_price": 38000,
        "min_margin": 0.08,
        "target_margin": 0.20,
        "metadata": {"brand": "Samsung", "display": "4K UHD"},
    },
    {
        "_id": "levis-501",
        "name": "Levi's 501 Original Jeans",
        "category": "clothing",
        "anchor_price": 4999,
        "cost_price": 2200,
        "min_margin": 0.12,
        "target_margin": 0.35,
        "metadata": {"brand": "Levi's", "fit": "Regular"},
    },
    {
        "_id": "boat-airdopes",
        "name": "boAt Airdopes 141 TWS Earbuds",
        "category": "electronics",
        "anchor_price": 1299,
        "cost_price": 450,
        "min_margin": 0.15,
        "target_margin": 0.40,
        "metadata": {"brand": "boAt", "type": "TWS"},
    },
]

PROMOTIONS = [
    {
        "_id": "promo-iphone-summer",
        "product_id": "iphone-15",
        "discount_percent": 5,
        "active": True,
        "valid_from": "2025-01-01T00:00:00Z",
        "valid_until": "2025-12-31T23:59:59Z",
        "description": "Summer sale — extra 5% off",
    },
    {
        "_id": "promo-boat-launch",
        "product_id": "boat-airdopes",
        "discount_percent": 10,
        "active": True,
        "valid_from": "2025-01-01T00:00:00Z",
        "valid_until": "2025-12-31T23:59:59Z",
        "description": "Launch offer — 10% off",
    },
]


async def seed() -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    for product in PRODUCTS:
        await db["products"].update_one(
            {"_id": product["_id"]}, {"$set": product}, upsert=True
        )
    print(f"Seeded {len(PRODUCTS)} products")

    for promo in PROMOTIONS:
        await db["promotions"].update_one(
            {"_id": promo["_id"]}, {"$set": promo}, upsert=True
        )
    print(f"Seeded {len(PROMOTIONS)} promotions")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
