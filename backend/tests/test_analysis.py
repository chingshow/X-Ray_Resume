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
            "shap_values", "salary_impact", "priority_skills",
            "analysis_id", "resume_snapshot", "job_snapshot"
        ]
        for field in required_fields:
            assert field in data, f"缺少欄位：{field}"

    async def test_analyze_match_score_range(self, client):
        """match_score 應在 0–100 之間"""
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

    async def test_analyze_multiple_times_upserts_same_record(self, client):
        """
        ✅ 改動：連續呼叫兩次分析，資料庫應該只有一筆（upsert 覆蓋）
        舊邏輯是累積兩筆，新邏輯是覆蓋同一筆 MOCK_ANALYSIS_ID
        """
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        await client.get("/analyze")
        await client.get("/analyze")

        results = (await client.get("/analysis-results")).json()
        # ✅ 現在預期是 1 筆，不是 2 筆
        assert len(results) == 1

    async def test_analyze_uses_fixed_analysis_id(self, client):
        """
        ✅ 新增：確認分析結果使用固定的 MOCK_ANALYSIS_ID
        """
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        data = (await client.get("/analyze")).json()
        assert data["analysis_id"] == "22222222-2222-2222-2222-222222222222"

    async def test_analyze_resume_snapshot_matches_seeded_data(self, client):
        """
        ✅ 新增：分析結果的 resume_snapshot 應與 seed 的資料一致
        """
        await client.post("/dev/seed-resume", json={"full_name": "測試求職者"})
        await client.post("/dev/seed-job", json={})
        data = (await client.get("/analyze")).json()
        assert data["resume_snapshot"]["full_name"] == "測試求職者"

    async def test_analyze_shap_values_sum_to_one(self, client):
        """
        ✅ 新增：shap_values 四個權重加總應等於 1.0
        """
        await client.post("/dev/seed-resume", json={})
        await client.post("/dev/seed-job", json={})
        data = (await client.get("/analyze")).json()
        shap = data["shap_values"]
        total = sum(shap.values())
        assert abs(total - 1.0) < 0.01, f"shap_values 加總為 {total}，應為 1.0"


class TestMatchJobByRole:
    """
    ✅ 全新：測試 match_job_by_role 職缺比對邏輯
    這是這版最重要的新功能，要獨立測試
    """

    async def test_match_job_selects_best_matching_job(self, client):
        """
        target_role 是「後端工程師」時，應該選到後端相關職缺
        而不是隨機選第一筆
        """
        # 新增兩個不同的職缺
        await client.post("/dev/seed-job", json={"title": "前端工程師"})
        await client.post("/dev/seed-job", json={"title": "資深後端工程師"})

        # 履歷的 target_role 是後端
        await client.post("/dev/seed-resume", json={
            "full_name": "後端求職者",
            "preferences": {"target_role": "後端工程師"}
        })

        data = (await client.get("/analyze")).json()
        # 應該選到「資深後端工程師」，不是「前端工程師」
        assert "後端" in data["job_snapshot"]["title"]

    async def test_match_job_fallback_when_no_target_role(self, client):
        """
        履歷沒有填 target_role 時，應該回傳第一筆職缺（不報錯）
        """
        await client.post("/dev/seed-resume", json={
            "full_name": "沒有目標職位的求職者",
            "preferences": {}
        })
        await client.post("/dev/seed-job", json={})
        response = await client.get("/analyze")
        # 應該正常回傳，不會因為沒有 target_role 就報錯
        assert response.status_code == 200

    async def test_match_job_with_slash_separated_roles(self, client):
        """
        target_role 用斜線分隔多個職位時，應該正確拆解比對
        例如「後端工程師 / 全端工程師」
        """
        await client.post("/dev/seed-job", json={"title": "全端工程師"})
        await client.post("/dev/seed-resume", json={
            "preferences": {"target_role": "後端工程師 / 全端工程師"}
        })
        data = (await client.get("/analyze")).json()

        # 確認有回傳 job_snapshot，且內容不是空的
        assert data.get("job_snapshot") is not None
        assert data["job_snapshot"].get("title") is not None