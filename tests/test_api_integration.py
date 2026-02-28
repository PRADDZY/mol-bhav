"""HTTP-level integration tests with mocked MongoDB and Redis."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# Helpers — mock the DB layer so we never need real Mongo / Redis
# ---------------------------------------------------------------------------

_fake_redis = MagicMock()
_fake_redis.set = AsyncMock()
_fake_redis.get = AsyncMock(return_value=None)
_fake_redis.delete = AsyncMock()
_fake_redis.exists = AsyncMock(return_value=False)
_fake_redis.incr = AsyncMock(return_value=1)
_fake_redis.expire = AsyncMock()
_fake_redis.ping = AsyncMock()

_fake_db = MagicMock()


@pytest.fixture()
def _patch_db():
    """Patch MongoDB and Redis so the app boots without external services."""
    with (
        patch("app.db.mongo.connect_mongo", new_callable=AsyncMock),
        patch("app.db.mongo.close_mongo", new_callable=AsyncMock),
        patch("app.db.mongo.get_db", return_value=_fake_db),
        patch("app.db.redis.connect_redis", new_callable=AsyncMock),
        patch("app.db.redis.close_redis", new_callable=AsyncMock),
        patch("app.db.redis.get_redis", return_value=_fake_redis),
        patch("app.db.redis.check_cooldown", new_callable=AsyncMock, return_value=False),
        patch("app.db.redis.set_cooldown", new_callable=AsyncMock),
        patch("app.db.redis.acquire_session_lock", new_callable=AsyncMock, return_value=True),
        patch("app.db.redis.release_session_lock", new_callable=AsyncMock),
        patch("app.db.redis.load_session", new_callable=AsyncMock, return_value=None),
    ):
        yield


@pytest.fixture()
async def client(_patch_db):
    from app.auth import verify_admin_key, verify_session_token
    from app.main import app

    # Override auth dependencies so tests don't need real tokens
    app.dependency_overrides[verify_admin_key] = lambda: "test-admin"
    app.dependency_overrides[verify_session_token] = lambda: "test-token"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Health endpoint returns valid JSON with expected fields."""
    resp = await client.get("/health")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert data["engine"] == "mol-bhav"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_has_request_id(client: AsyncClient):
    """Response includes X-Request-ID header from middleware."""
    resp = await client.get("/health")
    assert "x-request-id" in resp.headers


@pytest.mark.asyncio
async def test_health_preserves_custom_request_id(client: AsyncClient):
    """Middleware echoes caller-supplied X-Request-ID."""
    resp = await client.get("/health", headers={"X-Request-ID": "my-trace-123"})
    assert resp.headers["x-request-id"] == "my-trace-123"


@pytest.mark.asyncio
async def test_create_product_success(client: AsyncClient):
    """POST /products returns 201 on success."""
    mock_coll = MagicMock()
    mock_coll.insert_one = AsyncMock()

    with patch("app.api.products.products_collection", return_value=mock_coll):
        resp = await client.post(
            "/api/v1/products",
            json={
                "id": "test-prod-1",
                "name": "Test Product",
                "category": "testing",
                "anchor_price": 1000,
                "cost_price": 600,
                "min_margin": 0.10,
                "target_margin": 0.25,
            },
        )
    assert resp.status_code == 201
    assert resp.json()["id"] == "test-prod-1"


@pytest.mark.asyncio
async def test_create_product_duplicate(client: AsyncClient):
    """POST /products returns 409 on duplicate key."""
    from pymongo.errors import DuplicateKeyError

    mock_coll = MagicMock()
    mock_coll.insert_one = AsyncMock(side_effect=DuplicateKeyError("dup"))

    with patch("app.api.products.products_collection", return_value=mock_coll):
        resp = await client.post(
            "/api/v1/products",
            json={
                "id": "dup-prod",
                "name": "Dup Product",
                "category": "test",
                "anchor_price": 500,
                "cost_price": 300,
                "min_margin": 0.05,
                "target_margin": 0.15,
            },
        )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_product_invalid_id(client: AsyncClient):
    """POST /products rejects invalid product ID format."""
    resp = await client.post(
        "/api/v1/products",
        json={
            "id": "bad id with spaces!!",
            "name": "Bad",
            "anchor_price": 100,
            "cost_price": 50,
            "min_margin": 0.05,
            "target_margin": 0.10,
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient):
    """GET /products/{id} returns 404 when product doesn't exist."""
    mock_coll = MagicMock()
    mock_coll.find_one = AsyncMock(return_value=None)

    with patch("app.api.products.products_collection", return_value=mock_coll):
        resp = await client.get("/api/v1/products/no-such-item")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_product_invalid_id(client: AsyncClient):
    """GET /products/{id} rejects invalid product ID format."""
    resp = await client.get("/api/v1/products/bad id!!!")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_start_negotiation_product_not_found(client: AsyncClient):
    """Start negotiation with non-existent product → 404."""
    from app.api.deps import get_negotiation_service
    from app.main import app

    svc = AsyncMock()
    svc.start = AsyncMock(side_effect=ValueError("Product not found"))
    app.dependency_overrides[get_negotiation_service] = lambda: svc
    try:
        resp = await client.post(
            "/api/v1/negotiate/start",
            json={"product_id": "ghost", "buyer_name": "Test"},
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_offer_invalid_session_id(client: AsyncClient):
    """Offer with malformed session_id → 400."""
    resp = await client.post(
        "/api/v1/negotiate/not-a-valid-hex/offer",
        json={"message": "hello", "price": 100},
    )
    assert resp.status_code == 400
    assert "Invalid session ID" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_status_invalid_session_id(client: AsyncClient):
    """Status with malformed session_id → 400."""
    resp = await client.get(
        "/api/v1/negotiate/ZZZZ/status",
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_offer_missing_price(client: AsyncClient):
    """Offer without price field → 422 (validation error)."""
    session_id = "a" * 32
    resp = await client.post(
        f"/api/v1/negotiate/{session_id}/offer",
        json={"message": "hello"},
    )
    assert resp.status_code == 422
