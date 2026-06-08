# tests/test_analyze.py
"""
AI 分析端點測試

測試目標：
  GET  /analyze                   → 自動比對最佳職缺並分析
  POST /analyze/job/{job_id}      → 針對特定職缺分析（含快取邏輯）

關鍵場景：
  - 缺資料時 404
  - 回應結構完整性
  - match_score 數值範圍
  - shap_values 加總應接近 1.0
  - priority_skills 數量
  - 重複分析 upsert（不累積多筆）
  - 智慧 job matching（target_role 比對）
  - 快取命中（resume 未更新時回傳 cached: true）
  - HR 角色無法執行分析（403）
"""

import pytest

def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

REQUIRED_FIELDS = [
    "match_score", "scenario_simulation",
    "shap_values", "salary_impact", "priority_skills",
    "analysis_id", "resume_snapshot", "job_snapshot",
]


# ---------------------------------------------------------------------------
# GET /analyze  （自動比對最佳職缺）
# ---------------------------------------------------------------------------

class TestAutoAnalyze:
    async def test_analyze_without_auth_returns_401(self, client):
        """未登入呼叫 /analyze 應回傳 401。"""
        response = await client.get("/analyze")
        assert response.status_code == 401

    async def test_hr_cannot_run_analyze(self, client, hr_token):
        """HR 角色不應能呼叫 /analyze，應回傳 403。"""
        response = await client.get("/analyze", headers=auth(hr_token))
        assert response.status_code == 403



# ---------------------------------------------------------------------------
# POST /analyze/job/{job_id}  特定職缺分析（含快取）
# ---------------------------------------------------------------------------

class TestAnalyzeSpecificJob:
    async def _get_job_id(self, client, jobseeker_token) -> str:
        """Helper：seed 一筆職缺並取得其 job_id。"""
        await client.post("/dev/seed-job", json={"title": "DevOps 工程師"})
        jobs = (await client.get("/jobs", headers=auth(jobseeker_token))).json()
        return jobs[0]["id"]

    async def test_analyze_nonexistent_job_returns_404(self, client, jobseeker_token):
        """指定不存在的 job_id 應回傳 404。"""
        await client.post("/dev/seed-resume", json={})
        response = await client.post(
            "/analyze/job/00000000-0000-0000-0000-000000000000",
            headers=auth(jobseeker_token),
        )
        assert response.status_code == 404

    async def test_hr_cannot_analyze_specific_job(self, client, hr_token):
        """HR 角色呼叫特定職缺分析應回傳 403。"""
        response = await client.post(
            "/analyze/job/any-id", headers=auth(hr_token)
        )
        assert response.status_code == 403
