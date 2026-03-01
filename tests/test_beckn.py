"""Tests for Beckn /select endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


_fake_redis = MagicMock()
_fake_redis.set = AsyncMock()
_fake_redis.get = AsyncMock(return_value=None)
_fake_redis.delete = AsyncMock()
_fake_redis.exists = AsyncMock(return_value=False)
_fake_redis.incr = AsyncMock(return_value=1)
_fake_redis.expire = AsyncMock()
_fake_redis.ping = AsyncMock()

_fake_db = MagicMock()


def _make_nego_result(**overrides):
    """Build a MagicMock that looks like NegotiationResponse."""
    defaults = {
        "session_id": "abc123",
        "state": "responding",
        "current_price": 900.0,
        "quote_ttl_seconds": 60,
        "round": 1,
        "message": "Bhai, best price for you!",
        "metadata": {},
    }
    defaults.update(overrides)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    m.model_dump.return_value = defaults
    return m


@pytest.fixture()
def _patch_db():
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

    app.dependency_overrides[verify_admin_key] = lambda: "test-admin"
    app.dependency_overrides[verify_session_token] = lambda: "test-token"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


def _beckn_body(items=None, negotiation=None):
    """Build a minimal BecknSelectRequest body."""
    order = {"items": items or []}
    if negotiation:
        order["negotiation"] = negotiation
    return {
        "context": {"domain": "retail", "action": "select"},
        "message": {"order": order},
    }


class TestBecknSelect:
    @pytest.mark.asyncio
    async def test_empty_items_returns_400(self, client: AsyncClient):
        resp = await client.post("/beckn/select", json=_beckn_body(items=[]))
        assert resp.status_code == 400
        assert "No items" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_price_value_returns_400(self, client: AsyncClient):
        items = [{"id": "prod-1", "price": {"value": "not-a-number"}}]
        resp = await client.post("/beckn/select", json=_beckn_body(items=items))
        assert resp.status_code == 400
        assert "Invalid price" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_new_negotiation_success(self, client: AsyncClient):
        """New negotiation via Beckn returns on_select response."""
        from app.api.deps import get_negotiation_service
        from app.main import app

        mock_result = _make_nego_result()
        svc = AsyncMock()
        svc.start = AsyncMock(return_value=mock_result)
        app.dependency_overrides[get_negotiation_service] = lambda: svc

        try:
            items = [{"id": "prod-1", "price": {"value": "500"}}]
            resp = await client.post("/beckn/select", json=_beckn_body(items=items))
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        svc.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_new_negotiation_product_not_found(self, client: AsyncClient):
        from app.api.deps import get_negotiation_service
        from app.main import app

        svc = AsyncMock()
        svc.start = AsyncMock(side_effect=ValueError("Product not found"))
        app.dependency_overrides[get_negotiation_service] = lambda: svc

        try:
            items = [{"id": "ghost", "price": {"value": "100"}}]
            resp = await client.post("/beckn/select", json=_beckn_body(items=items))
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_continuation_with_session_id(self, client: AsyncClient):
        """When session_id is present, it follows the negotiate path."""
        from app.api.deps import get_negotiation_service
        from app.main import app

        mock_result = _make_nego_result(state="responding", current_price=850.0)
        svc = AsyncMock()
        svc.negotiate = AsyncMock(return_value=mock_result)
        app.dependency_overrides[get_negotiation_service] = lambda: svc

        try:
            items = [{"id": "prod-1", "price": {"value": "700"}, "tags": {"message": "aur kam karo"}}]
            resp = await client.post(
                "/beckn/select",
                json=_beckn_body(items=items, negotiation={"session_id": "sess-123"}),
            )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        svc.negotiate.assert_called_once()

    @pytest.mark.asyncio
    async def test_continuation_invalid_session(self, client: AsyncClient):
        from app.api.deps import get_negotiation_service
        from app.main import app

        svc = AsyncMock()
        svc.negotiate = AsyncMock(side_effect=ValueError("Session expired"))
        app.dependency_overrides[get_negotiation_service] = lambda: svc

        try:
            items = [{"id": "prod-1", "price": {"value": "500"}}]
            resp = await client.post(
                "/beckn/select",
                json=_beckn_body(items=items, negotiation={"session_id": "dead-session"}),
            )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 400
