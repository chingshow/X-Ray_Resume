import pytest


class TestSeedResume:
    async def test_seed_resume_default_values(self, client):
        """使用預設值初始化履歷應成功"""
        response = await client.post("/dev/seed-resume", json={})
        assert response.status_code == 200
        data = response.json()
        assert "resume_id" in data
        # ✅ 改動一：訊息文字已更新
        assert data["message"] == "測試履歷初始化/覆蓋成功"

    async def test_seed_resume_returns_fixed_uuid(self, client):
        """
        ✅ 新增：seed-resume 現在永遠回傳固定的 MOCK_RESUME_ID
        確認 upsert 邏輯正確，不是每次產生新的 UUID
        """
        response1 = await client.post("/dev/seed-resume", json={})
        response2 = await client.post("/dev/seed-resume", json={})
        id1 = response1.json()["resume_id"]
        id2 = response2.json()["resume_id"]
        # 兩次呼叫應該回傳同一個 ID
        assert id1 == id2
        # 確認是固定的 MOCK_RESUME_ID
        assert id1 == "11111111-1111-1111-1111-111111111111"

    async def test_seed_resume_custom_name(self, client):
        """可以傳入自訂姓名"""
        response = await client.post("/dev/seed-resume", json={"full_name": "李小華"})
        assert response.status_code == 200

    async def test_seed_resume_empty_skills(self, client):
        """技能清單可以是空陣列"""
        response = await client.post("/dev/seed-resume", json={"skills": []})
        assert response.status_code == 200

    async def test_seed_resume_overwrites_previous(self, client):
        """
        ✅ 新增：第二次 seed 應該覆蓋第一次的資料，不是新增一筆
        確認 upsert 機制正確運作
        """
        # 第一次：王小明
        await client.post("/dev/seed-resume", json={"full_name": "王小明"})
        # 第二次：李小華（覆蓋）
        await client.post("/dev/seed-resume", json={"full_name": "李小華"})

        # 跑分析，確認用的是最新的李小華
        await client.post("/dev/seed-job", json={})
        data = (await client.get("/analyze")).json()
        assert data["resume_snapshot"]["full_name"] == "李小華"


class TestCreateResume:
    async def test_post_resume_minimal(self, client):
        """
        ✅ 改動：POST /resume 狀態碼從 201 改為 200（upsert 語意）
        """
        response = await client.post("/resume", json={"full_name": "測試用戶"})
        assert response.status_code == 200

    async def test_post_resume_message(self, client):
        """✅ 新增：確認新的回傳訊息文字"""
        response = await client.post("/resume", json={"full_name": "測試用戶"})
        data = response.json()
        assert data["message"] == "履歷更新成功！(已覆蓋原有資料)"

    async def test_post_resume_full_payload(self, client):
        """POST /resume 完整欄位應成功並回傳資料"""
        payload = {
            "full_name": "陳大明",
            "education": "台灣大學 資工系",
            "skills": ["Python", "Docker"],
            "certifications": ["AWS"],
            "awards": [],
            "completion_rate": 75,
            "preferences": {"expected_salary": "80萬"}
        }
        response = await client.post("/resume", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    async def test_post_resume_empty_body(self, client):
        """POST /resume 空白 body 應成功（所有欄位 Optional）"""
        response = await client.post("/resume", json={})
        assert response.status_code == 200

    async def test_post_resume_uses_fixed_id(self, client):
        """
        ✅ 新增：確認 POST /resume 永遠使用固定的 MOCK_RESUME_ID
        不管呼叫幾次，資料庫都只有一筆履歷
        """
        await client.post("/resume", json={"full_name": "第一次"})
        await client.post("/resume", json={"full_name": "第二次"})
        response = await client.post("/resume", json={"full_name": "第三次"})
        data = response.json()
        assert data["data"]["id"] == "11111111-1111-1111-1111-111111111111"

    async def test_post_resume_invalid_completion_rate(self, client):
        """
        ✅ 新增：completion_rate 傳入字串應回傳 422
        確認 Pydantic 型別驗證有效
        """
        response = await client.post("/resume", json={"completion_rate": "不是數字"})
        assert response.status_code == 422