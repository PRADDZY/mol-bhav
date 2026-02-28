import asyncio
import logging

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_mongo(max_retries: int = 3) -> None:
    global _client, _db
    for attempt in range(1, max_retries + 1):
        try:
            _client = AsyncIOMotorClient(
                settings.mongodb_url,
                maxPoolSize=50,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000,
            )
            # Verify connectivity
            await _client.admin.command("ping")
            _db = _client[settings.mongodb_db_name]
            await _ensure_indexes()
            logger.info("MongoDB connected (attempt %d)", attempt)
            return
        except Exception:
            logger.warning("MongoDB connection attempt %d/%d failed", attempt, max_retries)
            if attempt == max_retries:
                raise
            await asyncio.sleep(2 ** attempt)


async def _ensure_indexes() -> None:
    """Create indexes for performance and TTL cleanup."""
    db = get_db()
    # Sessions — TTL on expires_at for automatic cleanup
    await db["sessions"].create_index("expires_at", expireAfterSeconds=0)
    # Negotiation logs — fast lookup by session + round
    await db["negotiation_logs"].create_index(
        [("session_id", pymongo.ASCENDING), ("round", pymongo.ASCENDING)]
    )
    # Products — category queries
    await db["products"].create_index("category")
    # Promotions — compound index for active-promo lookups
    await db["promotions"].create_index(
        [("product_id", pymongo.ASCENDING), ("active", pymongo.ASCENDING),
         ("valid_from", pymongo.ASCENDING), ("valid_until", pymongo.ASCENDING)]
    )
    logger.info("MongoDB indexes ensured")


async def close_mongo() -> None:
    global _client, _db
    if _client:
        _client.close()
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("MongoDB not connected. Call connect_mongo() first.")
    return _db


# --- Collection helpers ---

def sessions_collection():
    return get_db()["sessions"]


def products_collection():
    return get_db()["products"]


def negotiation_logs_collection():
    return get_db()["negotiation_logs"]


def promotions_collection():
    return get_db()["promotions"]
