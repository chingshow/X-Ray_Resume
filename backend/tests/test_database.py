# tests/test_database.py
import pytest

class TestDatabaseIntegrity:
    async def test_clear_removes_all_data(self, client):
        """DELETE /dev/clear 應清空所有資料表"""
        # 先建立資料
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        await client.get("/analyze")

        # 清空
        response = await client.delete("/dev/clear")
        assert response.status_code == 200

        # 確認分析結果已清空（analyze 應回傳 404）
        analyze_resp = await client.get("/analyze")
        assert analyze_resp.status_code == 404

    async def test_analysis_result_linked_to_resume_and_job(self, client):
        """analysis_results 應正確關聯 resume_id 和 job_id"""
        r1 = await client.post("/dev/seed-resume", json={})
        j1 = await client.post("/dev/seed-job", json={})
        await client.get("/analyze")

        results = (await client.get("/analysis-results")).json()
        assert len(results) == 1

        result = results[0]
        # 確認關聯 ID 存在（非空）
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
        assert response.status_code == 201
        
        saved = response.json()["data"]
        
        # 確認每個欄位都正確存入
        assert saved["full_name"] == "資料正確性測試"
        assert saved["skills"] == ["Python", "FastAPI"]
        assert saved["completion_rate"] == 80