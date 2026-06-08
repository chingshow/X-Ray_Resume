# tests/test_resume.py
"""
履歷 CRUD 測試

測試目標：
  POST /resume        → 新增 / 更新履歷（僅限 jobseeker）
  GET  /resume/me     → 取得自己的履歷

關鍵場景：
  - 未登入 → 401
  - HR 角色嘗試建立履歷 → 403
  - 成功建立、更新履歷
  - upsert 行為：同一 user 呼叫兩次只有一筆資料
  - 回應結構完整性
"""

import pytest

def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestResumeUpsert:
    async def test_upsert_resume_without_auth_returns_401(self, client):
        """未帶 Token 呼叫 POST /resume 應回傳 401。"""
        response = await client.post("/resume", json={"full_name": "無授權者"})
        assert response.status_code == 401

    async def test_hr_cannot_create_resume(self, client, hr_token):
        """HR 角色不允許建立履歷，應回傳 403。"""
        response = await client.post(
            "/resume",
            json={"full_name": "HR 帳號"},
            headers=auth(hr_token),
        )
        assert response.status_code == 403

    async def test_jobseeker_can_create_resume(self, client, jobseeker_token):
        """求職者成功建立履歷，應回傳 200 並包含 data 欄位。"""
        response = await client.post(
            "/resume",
            json={"full_name": "王小明", "education": "國立台灣大學"},
            headers=auth(jobseeker_token),
        )
        assert response.status_code == 200
        assert "data" in response.json()

    async def test_resume_upsert_is_idempotent(self, client, jobseeker_token):
        """同一求職者建立兩次履歷，應 upsert（只有一筆），不應產生重複資料。"""
        headers = auth(jobseeker_token)
        await client.post("/resume", json={"full_name": "初版姓名"}, headers=headers)
        await client.post("/resume", json={"full_name": "更新姓名"}, headers=headers)

        resp = await client.get("/resume/me", headers=headers)
        assert resp.status_code == 200
        # 只有一筆，且是最新版本
        assert resp.json()["data"]["full_name"] == "更新姓名"

    async def test_resume_partial_update_preserves_other_fields(self, client, jobseeker_token):
        """部分更新履歷時，未更新的欄位應保留原值。"""
        headers = auth(jobseeker_token)
        await client.post("/resume", json={
            "full_name": "李小華",
            "education": "政治大學",
            "skills": ["Python", "FastAPI"],
        }, headers=headers)

        # 只更新 full_name
        await client.post("/resume", json={"full_name": "李大華"}, headers=headers)

        data = (await client.get("/resume/me", headers=headers)).json()["data"]
        assert data["full_name"] == "李大華"
        # education 與 skills 應仍然存在（不被清空）
        assert data.get("education") == "政治大學"


class TestGetMyResume:
    async def test_get_resume_without_auth_returns_401(self, client):
        """未登入呼叫 GET /resume/me 應回傳 401。"""
        response = await client.get("/resume/me")
        assert response.status_code == 401

    async def test_get_resume_returns_saved_data(self, client, jobseeker_token):
        """建立後取得，應拿回相同的資料。"""
        headers = auth(jobseeker_token)
        await client.post("/resume", json={
            "full_name": "陳測試",
            "skills": ["React", "TypeScript"],
        }, headers=headers)

        data = (await client.get("/resume/me", headers=headers)).json()["data"]
        assert data["full_name"] == "陳測試"
        assert "React" in data["skills"]

    async def test_hr_cannot_access_resume_me(self, client, hr_token):
        """HR 角色不應能存取 /resume/me，應回傳 403。"""
        response = await client.get("/resume/me", headers=auth(hr_token))
        assert response.status_code == 403
