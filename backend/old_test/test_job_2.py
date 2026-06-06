# test_job.py 應該要測的東西
class TestSeedJob:
    async def test_seed_job_default_values(self, client):
        """用預設值新增職缺應該成功"""
        response = await client.post("/dev/seed-job", json={})
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["message"] == "測試履歷初始化/覆蓋成功"

    async def test_seed_job_returns_uuid(self, client):
        """回傳的 job_id 應該是合法 UUID"""
        import re
        response = await client.post("/dev/seed-job", json={})
        data = response.json()
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, data["job_id"])

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

    async def test_seed_job_null_title(self, client):
        """title 傳入 null 應該要報錯"""
        response = await client.post("/dev/seed-job", json={"title": None})
        assert response.status_code != 200