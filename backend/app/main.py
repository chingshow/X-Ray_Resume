import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
import math
import random

load_dotenv()

app = FastAPI(title="X-Ray Resume API", version="0.2.0")

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# ===========================================================================
# 🔧 開發測試專用：固定 ID 常數 (必須符合 UUID 格式)
# ===========================================================================
MOCK_RESUME_ID = "11111111-1111-1111-1111-111111111111"
MOCK_ANALYSIS_ID = "22222222-2222-2222-2222-222222222222"


# ===========================================================================
# Pydantic 實體模型群 (Data Schemas)
# ===========================================================================

class ResumeCreate(BaseModel):
    user_id: Optional[str] = None  # 設為 Optional 方便測試
    full_name: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    awards: Optional[List[str]] = None
    completion_rate: Optional[int] = 0
    preferences: Optional[Dict[str, Any]] = None


class DevResumeInput(BaseModel):
    full_name: str = "王小明"
    education: str = "國立台灣大學 資訊工程學系 學士"
    skills: list[str] = ["Python", "FastAPI", "PostgreSQL", "Docker"]
    certifications: list[str] = ["AWS Certified Cloud Practitioner"]
    awards: list[str] = ["2023 校內黑客松第二名"]
    completion_rate: Optional[int] = 80


class DevJobInput(BaseModel):
    title: str = "資深後端工程師"
    required_skills: list[str] = ["Python", "FastAPI", "Kubernetes", "Redis", "System Design"]
    salary_range: Optional[str] = "NT$1,000,000 – NT$1,500,000/年"
    min_experience: Optional[int] = 3


# ===========================================================================
# 基本路由
# ===========================================================================

@app.get("/")
def read_root():
    return {"message": "X-Ray Resume Backend is running!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ===========================================================================
# 📄 履歷管理 API (全面改為 Upsert 覆蓋機制)
# ===========================================================================

@app.post("/resume", status_code=status.HTTP_200_OK, tags=["📄 履歷管理"])
async def create_resume(resume_data: ResumeCreate):
    try:
        insert_data = resume_data.model_dump(exclude_unset=True)

        # 🔥 關鍵改動 1：強制綁定固定的履歷 ID，確保每次都是「覆蓋」同一筆
        insert_data["id"] = MOCK_RESUME_ID

        # 如果前端傳入測試用的非 UUID 字串，將其移除避免 Supabase 報外鍵錯誤
        if "user_id" in insert_data and insert_data["user_id"] == "test-user-123":
            insert_data.pop("user_id")

        # 🔥 關鍵改動 2：將 .insert() 改為 .upsert()
        response = supabase.table("resumes").upsert(insert_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="儲存履歷失敗，資料庫未返回結果"
            )

        return {
            "message": "履歷更新成功！(已覆蓋原有資料)",
            "data": response.data[0]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"伺服器錯誤: {str(e)}"
        )


# ===========================================================================
# 🔧 開發測試用 API
# ===========================================================================

@app.post("/dev/seed-resume", tags=["🔧 開發測試"])
def dev_seed_resume(data: DevResumeInput):
    """【測試用】一鍵初始化王小明的固定履歷"""
    payload = {
        "id": MOCK_RESUME_ID,  # 使用固定 ID
        "full_name": data.full_name,
        "education": data.education,
        "skills": data.skills,
        "certifications": data.certifications,
        "awards": data.awards,
        "completion_rate": data.completion_rate,
        "experience": [
            {"company": "新創科技股份有限公司", "title": "後端工程師", "duration": "2022/07 - 2024/06"},
            {"company": "學校專題實驗室", "title": "研究助理", "duration": "2021/09 - 2022/06"}
        ],
        "projects": [
            {"name": "X-Ray Resume", "url": "https://github.com/example/xray-resume"}
        ],
        "preferences": {"expected_salary": "NT$800,000/年", "target_role": "後端工程師 / 全端工程師"}
    }
    resp = supabase.table("resumes").upsert(payload).execute()  # 改為 upsert
    if not resp.data:
        raise HTTPException(status_code=500, detail="新增失敗")
    return {"message": "測試履歷初始化/覆蓋成功", "resume_id": resp.data[0]["id"]}


@app.post("/dev/seed-job", tags=["🔧 開發測試"])
def dev_seed_job(data: DevJobInput):
    """【測試用】一鍵初始化固定職缺"""
    # 職缺部分我們也可以給它一個固定 ID，方便對接
    MOCK_JOB_ID = "33333333-3333-3333-3333-333333333333"
    payload = {
        "id": MOCK_JOB_ID,
        "title": data.title,
        "required_skills": data.required_skills,
        "salary_range": data.salary_range,
        "min_experience": data.min_experience,
        "description": "負責設計與開發高併發後端服務，需具備雲端部署與系統架構設計能力。",
        "is_active": True,
    }
    resp = supabase.table("job_postings").upsert(payload).execute()  # 改為 upsert
    if not resp.data:
        raise HTTPException(status_code=500, detail="新增失敗")
    return {"message": "測試職缺初始化/覆蓋成功", "job_id": resp.data[0]["id"]}


@app.delete("/dev/clear", tags=["🔧 開發測試"])
def dev_clear():
    """【測試用】清空所有資料"""
    supabase.table("analysis_results").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("resumes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("job_postings").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    return {"message": "所有測試資料已清空"}


# ===========================================================================
# 📊 核心功能：AI 分析 (全面改為 Upsert 覆蓋機制)
# ===========================================================================

def mock_ai_analysis(resume: dict, job: dict) -> dict:
    """模擬 AI 回傳的分析結果 (保持不變)"""
    name = resume.get("full_name", "您")
    education = resume.get("education", "（未填寫）")
    skills = resume.get("skills") or []
    skills_str = "、".join(skills[:3]) if skills else "尚未填寫技能"

    required_skills = job.get("required_skills") or []
    missing_skills = [s for s in required_skills if s not in skills]
    missing_str = "、".join(missing_skills[:3]) if missing_skills else "無明顯缺口"
    job_title = job.get("title", "目標職位")

    return {
        "scenario_simulation": (
            f"根據 {name} 目前的履歷分析：您的學歷為「{education}」，"
            f"現有技能包含 {skills_str}。\n\n"
            f"【情境模擬】如果您補強「{missing_str}」，"
            f"預計可將與「{job_title}」職缺的匹配分數從目前的 62 分提升至 85 分（+23 分）。\n\n"
            f"【SHAP 分析原因】\n"
            f"- 技能匹配度（權重 45%）：您缺少 {missing_str}，此為該職缺核心要求，影響最大。\n"
            f"- 學歷符合度（權重 20%）：您的學歷「{education}」符合基本要求，正向貢獻分數。\n"
            f"- 工作經驗年資（權重 25%）：經歷尚在審核中，建議補充具體成果數字。\n"
            f"- 專案作品（權重 10%）：有附上作品連結，略有加分。"
        ),
        "shap_values": {
            "skill_match": 0.45,
            "education": 0.20,
            "experience": 0.25,
            "projects": 0.10
        },
        "salary_impact": (
            f"目前以您的技能組合（{skills_str}）在市場上預估年薪範圍約 NT$600,000 – NT$800,000。\n"
            f"若補強「{missing_str}」後，預估可提升至 NT$850,000 – NT$1,100,000（+25%）。\n"
            f"建議優先取得相關認證以加速薪資談判籌碼。"
        ),
        "priority_skills": [
            {"rank": 1, "skill": missing_skills[0] if len(missing_skills) > 0 else "雲端架構",
             "reason": "職缺必要技能，缺少影響分數最大"},
            {"rank": 2, "skill": missing_skills[1] if len(missing_skills) > 1 else "系統設計",
             "reason": "加分項目，可顯著提升競爭力"},
            {"rank": 3, "skill": missing_skills[2] if len(missing_skills) > 2 else "英文能力",
             "reason": "跨國職缺加分，長期職涯必備"},
        ],
        "match_score": random.randint(60, 85),
    }


@app.get("/analyze", tags=["📊 核心功能"])
def analyze_resume():
    """AI 分析 API (改為覆蓋舊有分析結果)"""
    # Step 1：取最新一筆履歷 (因為固定了 ID，這裡依然能拿到那唯一的一筆)
    resume_resp = supabase.table("resumes").select("*").order("updated_at", desc=True).limit(1).execute()
    if not resume_resp.data:
        raise HTTPException(status_code=404, detail="找不到履歷。請先至前端儲存履歷，或呼叫 /dev/seed-resume")
    resume = resume_resp.data[0]

    # Step 2：取最新一筆開放職缺
    job_resp = supabase.table("job_postings").select("*").eq("is_active", True).order("created_at", desc=True).limit(
        1).execute()
    if not job_resp.data:
        raise HTTPException(status_code=404, detail="找不到職缺。請先呼叫 POST /dev/seed-job 新增測試資料")
    job = job_resp.data[0]

    # Step 3：Mock AI 分析
    ai_result = mock_ai_analysis(resume, job)

    # 🔥 關鍵改動 3：封裝成帶有固定 MOCK_ANALYSIS_ID 的 payload，並改用 .upsert()
    analysis_payload = {
        "id": MOCK_ANALYSIS_ID,  # 強制覆蓋同一筆分析報告
        "resume_id": resume["id"],
        "job_id": job["id"],
        "match_score": ai_result["match_score"],
        "skill_gaps": [p["skill"] for p in ai_result["priority_skills"]],
        "explanation": ai_result["scenario_simulation"],
        "shap_values": ai_result["shap_values"],
        "salary_impact": ai_result["salary_impact"],
        "priority_skills": ai_result["priority_skills"],
    }

    save_resp = supabase.table("analysis_results").upsert(analysis_payload).execute()
    analysis_id = save_resp.data[0]["id"] if save_resp.data else None

    # Step 5：回傳
    return {
        "analysis_id": analysis_id,
        "resume_snapshot": {
            "full_name": resume.get("full_name"),
            "education": resume.get("education"),
            "skills": resume.get("skills"),
        },
        "job_snapshot": {
            "title": job.get("title"),
            "required_skills": job.get("required_skills"),
        },
        **ai_result,
    }


@app.get("/analysis-results", tags=["📊 核心功能"])
def list_analysis_results():
    """列出所有已儲存的分析結果"""
    response = supabase.table("analysis_results").select("*").order("created_at", desc=True).execute()
    return response.data