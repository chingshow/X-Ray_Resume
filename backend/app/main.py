import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

app = FastAPI(title="X-Ray Resume API", version="0.2.0")

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


# ===========================================================================
# Pydantic 實體模型群 (Data Schemas)
# ===========================================================================

# --- 完美對接 SQL 的 Pydantic 模型 (求職者端) ---
class ResumeCreate(BaseModel):
    user_id: Optional[str] = None                      # 對應 profiles(id)
    full_name: Optional[str] = None   # 姓名
    education: Optional[str] = None   # 學歷
    experience: Optional[List[Dict[str, Any]]] = None  # 工作經歷 (jsonb)
    skills: Optional[List[str]] = None                 # 技能關鍵詞 (text[])
    projects: Optional[List[Dict[str, Any]]] = None    # 專案作品連結 (jsonb)
    certifications: Optional[List[str]] = None         # 證照 (text[])
    awards: Optional[List[str]] = None                 # 獎項 (text[])
    completion_rate: Optional[int] = 0                 # 整體完成度
    preferences: Optional[Dict[str, Any]] = None       # 求職條件 (jsonb)


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
# 履歷管理 API (求職者端實質功能)
# ===========================================================================

# 實作精準對接的 POST /resume API
@app.post("/resume", status_code=status.HTTP_201_CREATED, tags=["📄 履歷管理"])
async def create_resume(resume_data: ResumeCreate):
    try:
        # 排除掉前端沒傳的欄位（保留資料庫的 Default 值，例如 id 和 updated_at）
        insert_data = resume_data.model_dump(exclude_unset=True)
        
        # 寫入 Supabase resumes 資料表
        response = supabase.table("resumes").insert(insert_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="儲存履歷失敗，資料庫未返回結果"
            )
            
        return {
            "message": "履歷儲存成功！",
            "data": response.data[0]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"伺服器錯誤: {str(e)}"
        )


# ===========================================================================
# 開發測試用：透過 API 直接輸入資料進資料庫
# （正式上線後可移除，改由前端履歷編輯頁面呼叫）
# ===========================================================================

@app.post("/dev/seed-resume", tags=["🔧 開發測試"])
def dev_seed_resume(data: DevResumeInput):
    """
    【開發測試用】直接透過此 API 新增一筆履歷到資料庫。
    欄位已有預設值，在 docs 點 Try it out → Execute 即可，不需修改任何內容。
    """
    payload = {
        "full_name": data.full_name,
        "education": data.education,
        "skills": data.skills,
        "certifications": data.certifications,
        "awards": data.awards,
        "completion_rate": data.completion_rate,
        # 簡化版：experience 和 projects 固定帶預設值，不需在 docs 輸入
        "experience": [
            {"company": "新創科技股份有限公司", "title": "後端工程師", "duration": "2022/07 - 2024/06"},
            {"company": "學校專題實驗室", "title": "研究助理", "duration": "2021/09 - 2022/06"}
        ],
        "projects": [
            {"name": "X-Ray Resume", "url": "https://github.com/example/xray-resume"}
        ],
        "preferences": {"expected_salary": "NT$800,000/年", "target_role": "後端工程師 / 全端工程師"}
    }
    resp = supabase.table("resumes").insert(payload).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="新增失敗")
    return {"message": "履歷新增成功", "resume_id": resp.data[0]["id"]}


@app.post("/dev/seed-job", tags=["🔧 開發測試"])
def dev_seed_job(data: DevJobInput):
    """
    【開發測試用】直接透過此 API 新增一筆職缺到資料庫。
    欄位已有預設值，在 docs 點 Try it out → Execute 即可。
    """
    payload = {
        "title": data.title,
        "required_skills": data.required_skills,
        "salary_range": data.salary_range,
        "min_experience": data.min_experience,
        "description": "負責設計與開發高併發後端服務，需具備雲端部署與系統架構設計能力。",
        "is_active": True,
    }
    resp = supabase.table("job_postings").insert(payload).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="新增失敗")
    return {"message": "職缺新增成功", "job_id": resp.data[0]["id"]}


@app.delete("/dev/clear", tags=["🔧 開發測試"])
def dev_clear():
    """
    【開發測試用】清空所有測試資料（analysis_results → resumes → job_postings）。
    方便重複測試時重置資料庫。
    """
    supabase.table("analysis_results").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("resumes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("job_postings").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    return {"message": "所有測試資料已清空"}


# ===========================================================================
# 核心 API：AI 分析（對應前端「履歷分析查看」頁面）
# ===========================================================================

def mock_ai_analysis(resume: dict, job: dict) -> dict:
    """
    模擬 AI 回傳的分析結果，內容帶入資料庫真實資料。

    ─────────────────────────────────────────────
    【未來串接真實 AI API 的替換方式】
    把 return 的內容換成：

        import httpx
        response = httpx.post(
            "https://your-ai-api.com/analyze",
            json={"resume": resume, "job": job},
            headers={"Authorization": f"Bearer {AI_API_KEY}"}
        )
        return response.json()

    回傳 JSON 結構保持相同，其他程式碼不需改動。
    ─────────────────────────────────────────────
    """
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
            {"rank": 1, "skill": missing_skills[0] if len(missing_skills) > 0 else "雲端架構", "reason": "職缺必要技能，缺少影響分數最大"},
            {"rank": 2, "skill": missing_skills[1] if len(missing_skills) > 1 else "系統設計", "reason": "加分項目，可顯著提升競爭力"},
            {"rank": 3, "skill": missing_skills[2] if len(missing_skills) > 2 else "英文能力", "reason": "跨國職缺加分，長期職涯必備"},
        ],
        "match_score": 62,
    }


@app.get("/analyze", tags=["📊 核心功能"])
def analyze_resume():
    """
    AI 分析 API（對應前端「履歷分析查看」頁面）

    流程：從資料庫取最新履歷 + 最新職缺 → Mock AI 分析 → 存入 analysis_results → 回傳

    ─────────────────────────────────────────────
    【未來有用戶登入後的寫法】
    @app.get("/analyze/{job_id}")
    def analyze_resume(job_id: str, current_user = Depends(get_current_user)):
        resume = supabase.table("resumes").select("*")
                    .eq("user_id", current_user.id).single().execute().data
        job = supabase.table("job_postings").select("*")
                    .eq("id", job_id).single().execute().data
        ...
    ─────────────────────────────────────────────
    """
    # Step 1：取最新一筆履歷
    resume_resp = supabase.table("resumes").select("*").order("updated_at", desc=True).limit(1).execute()
    if not resume_resp.data:
        raise HTTPException(status_code=404, detail="找不到履歷。請先呼叫 POST /dev/seed-resume 新增測試資料")
    resume = resume_resp.data[0]

    # Step 2：取最新一筆開放職缺
    job_resp = supabase.table("job_postings").select("*").eq("is_active", True).order("created_at", desc=True).limit(1).execute()
    if not job_resp.data:
        raise HTTPException(status_code=404, detail="找不到職缺。請先呼叫 POST /dev/seed-job 新增測試資料")
    job = job_resp.data[0]

    # Step 3：Mock AI 分析
    ai_result = mock_ai_analysis(resume, job)

    # Step 4：存入 analysis_results
    save_resp = supabase.table("analysis_results").insert({
        "resume_id": resume["id"],
        "job_id": job["id"],
        "match_score": ai_result["match_score"],
        "skill_gaps": [p["skill"] for p in ai_result["priority_skills"]],
        "explanation": ai_result["scenario_simulation"],
        "shap_values": ai_result["shap_values"],
        "salary_impact": ai_result["salary_impact"],
        "priority_skills": ai_result["priority_skills"],
    }).execute()

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
    """列出所有已儲存的分析結果，確認資料有寫入資料庫"""
    response = supabase.table("analysis_results").select("*").order("created_at", desc=True).execute()
    return response.data