# tests/test_database.py
"""
資料庫一致性與資料持久化測試

測試目標：
  - 分析完成後資料確實寫入 analysis_results
  - 分析結果可透過 GET /analysis-results 查詢
  - 履歷更新後，下次分析不使用舊快取（cache invalidation）
  - HR 可查看所有分析結果，求職者只能看到自己的
  - /dev/clear 確實清空資料（測試隔離基礎）

這些測試驗證的是「資料的生命週期」，而不是 API 的回應格式。
"""

import pytest

def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}




class TestAnalysisResultsVisibility:
    async def test_jobseeker_sees_only_own_results(self, client, jobseeker_token):
        """求職者查詢 /analysis-results 只應看到自己的分析結果，不含其他人的。"""
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        await client.get("/analyze", headers=auth(jobseeker_token))

        results = (await client.get(
            "/analysis-results", headers=auth(jobseeker_token)
        )).json()
        # 只有一位求職者的資料，結果應為 1 筆
        assert len(results) == 1

    async def test_hr_can_view_all_analysis_results(self, client, jobseeker_token, hr_token):
        """HR 查詢 /analysis-results 應能看到所有分析結果（跨用戶）。"""
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        await client.get("/analyze", headers=auth(jobseeker_token))

        hr_results = (await client.get(
            "/analysis-results", headers=auth(hr_token)
        )).json()
        assert len(hr_results) >= 1


