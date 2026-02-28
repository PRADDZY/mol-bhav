import json

import redis.asyncio as aioredis

from app.config import settings

_redis: aioredis.Redis | None = None


async def connect_redis() -> None:
    global _redis
    _redis = aioredis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.close()
    _redis = None


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not connected. Call connect_redis() first.")
    return _redis


# --- Session TTL helpers ---

def _key(session_id: str) -> str:
    return f"nego:session:{session_id}"


async def store_session(session_id: str, data: dict, ttl: int) -> None:
    r = get_redis()
    await r.set(_key(session_id), json.dumps(data, default=str), ex=ttl)


async def load_session(session_id: str) -> dict | None:
    r = get_redis()
    raw = await r.get(_key(session_id))
    if raw is None:
        return None
    return json.loads(raw)


async def delete_session(session_id: str) -> None:
    r = get_redis()
    await r.delete(_key(session_id))


async def session_exists(session_id: str) -> bool:
    r = get_redis()
    return bool(await r.exists(_key(session_id)))


async def refresh_ttl(session_id: str, ttl: int) -> None:
    r = get_redis()
    await r.expire(_key(session_id), ttl)


# --- Rate-limit / cooldown helpers ---

def _cooldown_key(session_id: str) -> str:
    return f"nego:cooldown:{session_id}"


async def check_cooldown(session_id: str) -> bool:
    """Returns True if still in cooldown (should block)."""
    r = get_redis()
    return bool(await r.exists(_cooldown_key(session_id)))


async def set_cooldown(session_id: str, ms: int) -> None:
    r = get_redis()
    await r.set(_cooldown_key(session_id), "1", px=ms)
