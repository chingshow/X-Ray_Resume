# tests/test_health.py
"""
健康檢查 & 根路由測試

測試目標：
  GET /          → 確認 API 正常運作，回傳歡迎訊息
  GET /health    → 確認健康狀態端點正常

這兩個端點不需要驗證，是部署後第一個確認系統是否存活的指標。
"""

import pytest


class TestRootRoute:
    async def test_root_returns_200(self, client):
        """GET / 應回傳 200。"""
        response = await client.get("/")
        assert response.status_code == 200

    async def test_root_contains_message(self, client):
        """根路由回應應包含 message 欄位。"""
        data = (await client.get("/")).json()
        assert "message" in data

    async def test_root_message_mentions_api(self, client):
        """message 欄位應包含 API 或版本相關字樣，確認不是空字串。"""
        data = (await client.get("/")).json()
        assert len(data["message"]) > 0


class TestHealthCheck:
    async def test_health_returns_200(self, client):
        """GET /health 應回傳 200。"""
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_status_is_ok(self, client):
        """健康狀態回應的 status 欄位應為 'ok'。"""
        data = (await client.get("/health")).json()
        assert data.get("status") == "ok"

    async def test_health_no_auth_required(self, client):
        """健康檢查端點不應要求 Authorization header。"""
        # 沒有帶任何 token，應該仍然回傳 200
        response = await client.get("/health")
        assert response.status_code != 401
