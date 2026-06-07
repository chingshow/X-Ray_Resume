# tests/test_health.py
import pytest

class TestHealthCheck:
    async def test_health_returns_200(self, client):
        """確認伺服器活著"""
        response = await client.get("/health")
        assert response.status_code == 200 # 如果不是200就報錯

    async def test_health_returns_ok_status(self, client):
        """確認內容是對的"""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    async def test_root_returns_200(self, client):
        """確認最基本的入口點是正常的"""
        response = await client.get("/")
        assert response.status_code == 200 