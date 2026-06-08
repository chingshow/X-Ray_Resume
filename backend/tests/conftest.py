# tests/conftest.py
"""
共用 fixtures：
  - client          → 每個測試用的 HTTP 客戶端
  - jobseeker_token → 已登入的求職者 Bearer Token
  - hr_token        → 已登入的 HR Bearer Token
  - clean_db        → 每個測試前後自動清空 DB（autouse）

所有測試都依賴 /dev/* 開發路由，請確認 app 有掛載這些路由。
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

# ---------------------------------------------------------------------------
# 基本 HTTP 客戶端
# ---------------------------------------------------------------------------

@pytest.fixture
async def client():
    """每個測試共用的 HTTP 測試客戶端，不需要真正啟動伺服器。"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# 資料庫清理（每個測試前後執行）
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
async def clean_db(client):
    """每個測試開始前清空資料庫，確保測試彼此獨立。"""
    await client.delete("/dev/clear")
    yield
    await client.delete("/dev/clear")


# ---------------------------------------------------------------------------
# 已登入的求職者 Token（需要 /dev/seed-user 或 /auth/register + /auth/login）
# ---------------------------------------------------------------------------

@pytest.fixture
async def jobseeker_token(client) -> str:
    """
    建立一位求職者並取回 Bearer Token。
    依賴 /dev/seed-user 快速建立帳號；若無此路由，改用 register + login。
    """
    # 方案 A：用 dev seed（快）
    resp = await client.post("/dev/seed-user", json={"role": "jobseeker"})
    if resp.status_code == 200:
        return resp.json().get("token", "")

    # 方案 B：register + login（相容無 seed-user 路由的環境）
    username = "test_jobseeker"
    password = "Test1234!"
    await client.post("/auth/register", json={
        "display_name": "測試求職者",
        "username": username,
        "password": password,
        "role": "jobseeker",
    })
    login_resp = await client.post("/auth/login", json={
        "username": username,
        "password": password,
    })
    return login_resp.json().get("token", "")


@pytest.fixture
async def hr_token(client) -> str:
    """
    建立一位 HR 並取回 Bearer Token。
    """
    resp = await client.post("/dev/seed-user", json={"role": "hr"})
    if resp.status_code == 200:
        return resp.json().get("token", "")

    username = "test_hr"
    password = "Test1234!"
    await client.post("/auth/register", json={
        "display_name": "測試HR",
        "username": username,
        "password": password,
        "role": "hr",
    })
    login_resp = await client.post("/auth/login", json={
        "username": username,
        "password": password,
    })
    return login_resp.json().get("token", "")


# ---------------------------------------------------------------------------
# 便利 helpers：帶 Auth header 的 client wrapper
# ---------------------------------------------------------------------------

def auth(token: str) -> dict:
    """回傳帶有 Bearer Token 的 header dict，方便傳給 httpx。"""
    return {"Authorization": f"Bearer {token}"}
