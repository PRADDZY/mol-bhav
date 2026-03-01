"""End-to-end negotiation flow: /start → /offer → /status.

Uses dependency overrides so no real DB/Redis/NIM is needed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.services.negotiation_service import NegotiationResponse


# ---------------------------------------------------------------------------
# Stubs
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


def _nego_resp(**overrides) -> NegotiationResponse:
    defaults = dict(
        session_id="aabbccdd11223344aabbccdd11223344",
        session_token="tok-xyz",
        message="Bhai, best price for you!",
        current_price=900.0,
        anchor_price=1000.0,
        state="responding",
        tactic="concession",
        sentiment="friendly",
        round=1,
        max_rounds=5,
        quote_ttl_seconds=60,
    )
    defaults.update(overrides)
    return NegotiationResponse(**defaults)


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


@pytest.mark.asyncio
async def test_full_negotiation_flow(client: AsyncClient):
    """Start → Offer → Status: full happy-path flow."""
    from app.api.deps import get_negotiation_service
    from app.main import app
    from app.models.session import NegotiationSession, NegotiationState

    svc = AsyncMock()

    # Step 1: /start — returns opening response
    start_resp = _nego_resp(round=0, state="responding")
    svc.start = AsyncMock(return_value=start_resp)

    app.dependency_overrides[get_negotiation_service] = lambda: svc

    try:
        resp = await client.post(
            "/api/v1/negotiate/start",
            json={"product_id": "prod-1", "buyer_name": "Rahul"},
        )
    finally:
        app.dependency_overrides.pop(get_negotiation_service, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "aabbccdd11223344aabbccdd11223344"
    assert data["state"] == "responding"
    assert data["current_price"] == 900.0
    svc.start.assert_called_once()

    # Step 2: /offer — buyer makes a counter offer
    offer_resp = _nego_resp(round=1, current_price=850.0, state="responding")
    svc.negotiate = AsyncMock(return_value=offer_resp)

    app.dependency_overrides[get_negotiation_service] = lambda: svc

    try:
        resp = await client.post(
            "/api/v1/negotiate/aabbccdd11223344aabbccdd11223344/offer",
            json={"price": 700, "message": "thoda aur kam karo"},
        )
    finally:
        app.dependency_overrides.pop(get_negotiation_service, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["current_price"] == 850.0
    assert data["round"] == 1
    svc.negotiate.assert_called_once()

    # Step 3: /status — check session status
    mock_session = MagicMock(spec=NegotiationSession)
    mock_session.session_id = "aabbccdd11223344aabbccdd11223344"
    mock_session.state = NegotiationState.RESPONDING
    mock_session.current_round = 1
    mock_session.max_rounds = 5
    mock_session.current_seller_price = 850.0
    mock_session.agreed_price = None
    mock_session.bot_score = 0.1

    svc.load_session = AsyncMock(return_value=mock_session)

    app.dependency_overrides[get_negotiation_service] = lambda: svc

    try:
        resp = await client.get("/api/v1/negotiate/aabbccdd11223344aabbccdd11223344/status")
    finally:
        app.dependency_overrides.pop(get_negotiation_service, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "aabbccdd11223344aabbccdd11223344"
    assert data["state"] == "responding"
    assert data["current_round"] == 1
    assert data["current_seller_price"] == 850.0


@pytest.mark.asyncio
async def test_offer_on_expired_session(client: AsyncClient):
    """Offer on an expired session returns 400."""
    from app.api.deps import get_negotiation_service
    from app.main import app

    svc = AsyncMock()
    svc.negotiate = AsyncMock(side_effect=ValueError("Session not found or expired"))
    app.dependency_overrides[get_negotiation_service] = lambda: svc

    try:
        resp = await client.post(
            "/api/v1/negotiate/aabbccdd11223344aabbccdd11223345/offer",
            json={"price": 500, "message": "hello"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_status_on_missing_session(client: AsyncClient):
    """Status on a missing session returns 404."""
    from app.api.deps import get_negotiation_service
    from app.main import app

    svc = AsyncMock()
    svc.load_session = AsyncMock(return_value=None)
    app.dependency_overrides[get_negotiation_service] = lambda: svc

    try:
        resp = await client.get("/api/v1/negotiate/aabbccdd11223344aabbccdd11223346/status")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
