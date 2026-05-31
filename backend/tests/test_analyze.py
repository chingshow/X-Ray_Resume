# tests/test_analyze.py
import pytest

class TestAnalyze:
    async def test_analyze_without_data_returns_404(self, client):
        """沒有資料時呼叫分析應回傳 404"""
        response = await client.get("/analyze")
        assert response.status_code == 404

    async def test_analyze_without_resume_returns_404(self, client):
        """只有職缺、沒有履歷時應回傳 404"""
        await client.post("/dev/seed-job", json={})
        response = await client.get("/analyze")
        assert response.status_code == 404

    async def test_analyze_without_job_returns_404(self, client):
        """只有履歷、沒有職缺時應回傳 404"""
        await client.post("/dev/seed-resume", json={})
        response = await client.get("/analyze")
        assert response.status_code == 404

    async def test_analyze_with_full_data_returns_200(self, client):
        """有履歷和職缺時分析應成功"""
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        response = await client.get("/analyze")
        assert response.status_code == 200

    async def test_analyze_response_structure(self, client):
        """分析結果應包含所有必要欄位"""
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        data = (await client.get("/analyze")).json()

        required_fields = [
            "match_score", "scenario_simulation",
            "shap_values", "salary_impact", "priority_skills"
        ]
        for field in required_fields:
            assert field in data, f"缺少欄位：{field}"

    async def test_analyze_match_score_range(self, client):
        """match_score 應在 0–100 之間"""
        ### 目前統一62分，所以都會通過
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        data = (await client.get("/analyze")).json()
        assert 0 <= data["match_score"] <= 100

    async def test_analyze_priority_skills_count(self, client):
        """priority_skills 應回傳 3 個優先技能"""
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        data = (await client.get("/analyze")).json()
        assert len(data["priority_skills"]) == 3

    async def test_analyze_saves_to_database(self, client):
        """分析完成後資料應寫入資料庫"""
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        await client.get("/analyze")

        results = (await client.get("/analysis-results")).json()
        assert len(results) >= 1

    async def test_analyze_multiple_times_accumulates(self, client):
        """多次分析應產生多筆 analysis_results"""
        # 但未來不排除會增加「判斷是否有更新」的功能
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        await client.get("/analyze")
        await client.get("/analyze")

        results = (await client.get("/analysis-results")).json()
        assert len(results) == 2