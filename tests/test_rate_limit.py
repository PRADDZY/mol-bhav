"""Tests for per-IP rate limiting in negotiate routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import HTTPException

from app.api.negotiate import _check_ip_rate_limit


@pytest.fixture()
def fake_redis():
    r = MagicMock()
    r.incr = AsyncMock(return_value=1)
    r.expire = AsyncMock()
    return r


class TestIPRateLimit:
    @pytest.mark.asyncio
    async def test_first_request_allowed(self, fake_redis):
        fake_redis.incr = AsyncMock(return_value=1)
        with patch("app.api.negotiate.get_redis", return_value=fake_redis), \
             patch("app.api.negotiate.settings") as mock_settings:
            mock_settings.max_requests_per_minute_per_ip = 10
            await _check_ip_rate_limit("192.168.1.1")
        fake_redis.incr.assert_called_once()
        fake_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_within_limit_allowed(self, fake_redis):
        fake_redis.incr = AsyncMock(return_value=5)
        with patch("app.api.negotiate.get_redis", return_value=fake_redis), \
             patch("app.api.negotiate.settings") as mock_settings:
            mock_settings.max_requests_per_minute_per_ip = 10
            await _check_ip_rate_limit("192.168.1.1")

    @pytest.mark.asyncio
    async def test_exceeds_limit_raises_429(self, fake_redis):
        fake_redis.incr = AsyncMock(return_value=11)
        with patch("app.api.negotiate.get_redis", return_value=fake_redis), \
             patch("app.api.negotiate.settings") as mock_settings:
            mock_settings.max_requests_per_minute_per_ip = 10
            with pytest.raises(HTTPException) as exc_info:
                await _check_ip_rate_limit("192.168.1.1")
            assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_expire_only_on_first_request(self, fake_redis):
        """Expire is only called when count == 1 (key created for first time)."""
        fake_redis.incr = AsyncMock(return_value=3)
        with patch("app.api.negotiate.get_redis", return_value=fake_redis), \
             patch("app.api.negotiate.settings") as mock_settings:
            mock_settings.max_requests_per_minute_per_ip = 10
            await _check_ip_rate_limit("192.168.1.1")
        fake_redis.expire.assert_not_called()

    @pytest.mark.asyncio
    async def test_exact_limit_allowed(self, fake_redis):
        """Request at exactly the limit should still be allowed."""
        fake_redis.incr = AsyncMock(return_value=10)
        with patch("app.api.negotiate.get_redis", return_value=fake_redis), \
             patch("app.api.negotiate.settings") as mock_settings:
            mock_settings.max_requests_per_minute_per_ip = 10
            await _check_ip_rate_limit("192.168.1.1")
