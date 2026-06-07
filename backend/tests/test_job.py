import pytest
import re


class TestSeedJob:
    async def test_seed_job_default_values(self, client):
        """使用預設值新增職缺應成功"""
        response = await client.post("/dev/seed-job", json={})
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        # ✅ 改動：訊息文字已更新
        assert data["message"] == "測試職缺新增成功"

    async def test_seed_job_returns_uuid(self, client):
        """回傳的 job_id 應為合法 UUID 格式"""
        response = await client.post("/dev/seed-job", json={})
        data = response.json()
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, data["job_id"])

    async def test_seed_job_creates_new_record_each_time(self, client):
        """
        ✅ 新增：seed-job 每次應產生不同的 UUID（不再使用固定 ID）
        與 seed-resume 的 upsert 行為相反，職缺是每次新增一筆
        """
        response1 = await client.post("/dev/seed-job", json={})
        response2 = await client.post("/dev/seed-job", json={})
        id1 = response1.json()["job_id"]
        id2 = response2.json()["job_id"]
        # 兩次呼叫應該是不同的 ID
        assert id1 != id2

    async def test_seed_job_custom_title(self, client):
        """可以傳入自訂職缺名稱"""
        response = await client.post("/dev/seed-job", json={"title": "前端工程師"})
        assert response.status_code == 200

    async def test_seed_job_custom_skills(self, client):
        """可以傳入自訂必要技能"""
        response = await client.post("/dev/seed-job", json={
            "required_skills": ["React", "TypeScript"]
        })
        assert response.status_code == 200

    async def test_seed_job_null_title_should_fail(self, client):
        """
        ✅ 新增：title 是資料庫 NOT NULL 欄位
        傳入 null 應該要報錯，不能成功儲存
        """
        response = await client.post("/dev/seed-job", json={"title": None})
        assert response.status_code != 200