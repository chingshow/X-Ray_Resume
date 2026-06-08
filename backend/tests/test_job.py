# tests/test_job.py
"""
職缺 CRUD & 投遞測試

測試目標：
  GET  /jobs                              → 列出所有職缺（需登入）
  POST /jobs                              → 建立職缺（僅限 HR）
  GET  /jobs/my                           → HR 查看自己的職缺
  GET  /jobs/{job_id}/applications        → HR 查看特定職缺的投遞清單
  POST /applications                      → 求職者投遞職缺
  GET  /applications/my                   → 求職者查看自己的投遞紀錄

關鍵場景：
  - 角色權限邊界（403）
  - 重複投遞防護（409）
  - 沒有履歷就投遞（400）
  - 投遞已關閉職缺（404）
"""

import pytest

def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestListJobs:
    async def test_list_jobs_without_auth_returns_401(self, client):
        """未登入不得列出職缺。"""
        response = await client.get("/jobs")
        assert response.status_code == 401

    async def test_list_jobs_returns_list(self, client, jobseeker_token):
        """登入後呼叫 GET /jobs 應回傳陣列（可為空）。"""
        response = await client.get("/jobs", headers=auth(jobseeker_token))
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestCreateJob:
    async def test_jobseeker_cannot_create_job(self, client, jobseeker_token):
        """求職者不得建立職缺，應回傳 403。"""
        response = await client.post(
            "/jobs",
            json={"title": "前端工程師"},
            headers=auth(jobseeker_token),
        )
        assert response.status_code == 403

    async def test_hr_can_create_job(self, client, hr_token):
        """HR 成功建立職缺，應回傳 201 並包含 data 欄位。"""
        response = await client.post(
            "/jobs",
            json={
                "title": "全端工程師",
                "company": "測試科技",
                "required_skills": ["React", "FastAPI"],
                "min_experience": 2,
            },
            headers=auth(hr_token),
        )
        assert response.status_code == 201
        assert "data" in response.json()

    async def test_create_job_missing_title_returns_error(self, client, hr_token):
        """title 為必填，缺少時應回傳 4xx 錯誤。"""
        response = await client.post(
            "/jobs",
            json={"company": "無名公司"},
            headers=auth(hr_token),
        )
        assert response.status_code in (400, 422)


class TestMyJobs:
    async def test_hr_can_list_own_jobs(self, client, hr_token):
        """HR 建立職缺後，GET /jobs/my 應能看到自己建立的職缺。"""
        await client.post(
            "/jobs",
            json={"title": "數據分析師"},
            headers=auth(hr_token),
        )
        jobs = (await client.get("/jobs/my", headers=auth(hr_token))).json()
        assert any(j["title"] == "數據分析師" for j in jobs)

    async def test_my_jobs_includes_application_count(self, client, hr_token):
        """GET /jobs/my 的每筆職缺應包含 application_count 欄位。"""
        await client.post("/jobs", json={"title": "PM職缺"}, headers=auth(hr_token))
        jobs = (await client.get("/jobs/my", headers=auth(hr_token))).json()
        for job in jobs:
            assert "application_count" in job
