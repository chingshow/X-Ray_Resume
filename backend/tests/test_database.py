import pytest


class TestDatabaseIntegrity:
    async def test_clear_removes_all_data(self, client):
        """DELETE /dev/clear 應清空所有資料表"""
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        await client.get("/analyze")

        response = await client.delete("/dev/clear")
        assert response.status_code == 200

        analyze_resp = await client.get("/analyze")
        assert analyze_resp.status_code == 404

    async def test_analysis_result_linked_to_resume_and_job(self, client):
        """analysis_results 應正確關聯 resume_id 和 job_id"""
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        await client.get("/analyze")

        results = (await client.get("/analysis-results")).json()
        assert len(results) == 1

        result = results[0]
        assert result["resume_id"] is not None
        assert result["job_id"] is not None

    async def test_analysis_result_has_required_db_fields(self, client):
        """analysis_results 資料庫記錄應包含所有必要欄位"""
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        await client.get("/analyze")

        results = (await client.get("/analysis-results")).json()
        record = results[0]

        db_fields = ["id", "resume_id", "job_id", "match_score",
                     "skill_gaps", "explanation", "shap_values",
                     "salary_impact", "priority_skills", "created_at"]
        for field in db_fields:
            assert field in record, f"資料庫記錄缺少欄位：{field}"

    async def test_resume_data_correctness(self, client):
        """確認寫進資料庫的內容和送出的內容一致"""
        payload = {
            "full_name": "資料正確性測試",
            "skills": ["Python", "FastAPI"],
            "completion_rate": 80
        }
        response = await client.post("/resume", json=payload)
        # ✅ 改動：狀態碼已從 201 改為 200
        assert response.status_code == 200

        saved = response.json()["data"]
        assert saved["full_name"] == "資料正確性測試"
        assert saved["skills"] == ["Python", "FastAPI"]
        assert saved["completion_rate"] == 80

    async def test_analysis_result_uses_fixed_mock_id(self, client):
        """
        ✅ 新增：確認 analysis_results 使用固定的 MOCK_ANALYSIS_ID
        這是 upsert 機制的核心，確保資料庫只有一筆分析記錄
        """
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        await client.get("/analyze")

        results = (await client.get("/analysis-results")).json()
        assert results[0]["id"] == "22222222-2222-2222-2222-222222222222"

    async def test_upsert_overwrites_previous_analysis(self, client):
        """
        ✅ 新增：第二次分析應該覆蓋第一次，資料庫只保留最新一筆
        確認 upsert 機制不會產生重複資料
        """
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})

        # 第一次分析
        await client.get("/analyze")
        results_after_first = (await client.get("/analysis-results")).json()
        assert len(results_after_first) == 1

        # 第二次分析
        await client.get("/analyze")
        results_after_second = (await client.get("/analysis-results")).json()
        # 應該還是 1 筆，不是 2 筆
        assert len(results_after_second) == 1