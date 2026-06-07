# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    """每個測試共用的 HTTP 測試客戶端，不需要真正啟動伺服器"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture(autouse=True)
async def clean_db(client):
    """每個測試前自動清空資料庫，確保測試互相獨立"""
    await client.delete("/dev/clear")
    yield
    # 測試結束後也清一次（選擇性）
    await client.delete("/dev/clear")