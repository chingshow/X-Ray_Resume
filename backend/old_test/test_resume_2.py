# tests/test_resume.py
import pytest

class TestSeedResume:
    async def test_seed_resume_default_values(self, client):
        """使用預設值新增履歷應成功"""
        response = await client.post("/dev/seed-resume", json={})
        assert response.status_code == 200
        data = response.json()
        assert "resume_id" in data
        assert data["message"] == "測試職缺新增成功"

    async def test_seed_resume_returns_uuid(self, client):
        """回傳的 resume_id 應為合法 UUID 格式"""
        import re
        response = await client.post("/dev/seed-resume", json={})
        data = response.json()
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, data["resume_id"])

    async def test_seed_resume_custom_name(self, client):
        """可以傳入自訂姓名"""
        response = await client.post("/dev/seed-resume", json={"full_name": "李小華"})
        assert response.status_code == 200

    async def test_seed_resume_empty_skills(self, client):
        """技能清單可以是空陣列"""
        response = await client.post("/dev/seed-resume", json={"skills": []})
        assert response.status_code == 200




class TestCreateResume:
    async def test_post_resume_minimal(self, client):
        """POST /resume 確認 Optional 欄位不填也能成功"""
        response = await client.post("/resume", json={"full_name": "測試用戶"})
        assert response.status_code == 201

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
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "履歷儲存成功！"
        assert "data" in data

    async def test_post_resume_empty_body(self, client):
        """POST /resume 空白 body 應成功（所有欄位 Optional）"""
        response = await client.post("/resume", json={})
        assert response.status_code == 201