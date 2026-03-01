"""Unit tests for auth dependencies."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.auth import verify_admin_key, verify_session_token


# ---------------------------------------------------------------------------
# verify_admin_key
# ---------------------------------------------------------------------------

class TestVerifyAdminKey:
    @pytest.mark.asyncio
    async def test_valid_key(self):
        with patch("app.auth.settings") as mock_settings:
            mock_settings.api_admin_key = "secret-admin-key"
            result = await verify_admin_key("secret-admin-key")
        assert result == "secret-admin-key"

    @pytest.mark.asyncio
    async def test_invalid_key(self):
        with patch("app.auth.settings") as mock_settings:
            mock_settings.api_admin_key = "secret-admin-key"
            with pytest.raises(HTTPException) as exc_info:
                await verify_admin_key("wrong-key")
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_admin_key_dev_mode(self):
        """When API_ADMIN_KEY is not configured, returns 'dev' (dev mode)."""
        with patch("app.auth.settings") as mock_settings:
            mock_settings.api_admin_key = ""
            result = await verify_admin_key("anything")
        assert result == "dev"

    @pytest.mark.asyncio
    async def test_none_admin_key_dev_mode(self):
        with patch("app.auth.settings") as mock_settings:
            mock_settings.api_admin_key = None
            result = await verify_admin_key("anything")
        assert result == "dev"

    @pytest.mark.asyncio
    async def test_timing_safe_comparison(self):
        """Ensure timing-safe comparison is used (secrets.compare_digest)."""
        with patch("app.auth.settings") as mock_settings, \
             patch("app.auth.secrets.compare_digest", return_value=True) as mock_compare:
            mock_settings.api_admin_key = "key"
            await verify_admin_key("key")
            mock_compare.assert_called_once_with("key", "key")


# ---------------------------------------------------------------------------
# verify_session_token
# ---------------------------------------------------------------------------

class TestVerifySessionToken:
    @pytest.mark.asyncio
    async def test_valid_token(self):
        with patch("app.db.redis.load_session", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = {"session_token": "tok-123"}
            result = await verify_session_token("sess-abc", "tok-123")
        assert result == "tok-123"

    @pytest.mark.asyncio
    async def test_session_not_found(self):
        with patch("app.db.redis.load_session", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                await verify_session_token("no-such-session", "tok-123")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_wrong_token(self):
        with patch("app.db.redis.load_session", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = {"session_token": "correct-token"}
            with pytest.raises(HTTPException) as exc_info:
                await verify_session_token("sess-abc", "wrong-token")
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_stored_token(self):
        """If stored token is empty string, reject."""
        with patch("app.db.redis.load_session", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = {"session_token": ""}
            with pytest.raises(HTTPException) as exc_info:
                await verify_session_token("sess-abc", "any-token")
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_token_key(self):
        """If session data has no session_token key, reject."""
        with patch("app.db.redis.load_session", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = {"other_data": "value"}
            with pytest.raises(HTTPException) as exc_info:
                await verify_session_token("sess-abc", "any-token")
            assert exc_info.value.status_code == 403
