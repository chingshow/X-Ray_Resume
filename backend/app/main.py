import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
import math
import random
from google import genai
from google.genai import types
import json
import re



load_dotenv()

app = FastAPI(title="X-Ray Resume API", version="0.2.0")
# 在 load_dotenv() 之後加入
gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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
    """【測試用】新增一筆職缺（每次都是全新一筆，不再覆蓋）"""
    payload = {
        # 移除 "id": MOCK_JOB_ID 這行，讓 Supabase 自動產生 UUID
        "title": data.title,
        "required_skills": data.required_skills,
        "salary_range": data.salary_range,
        "min_experience": data.min_experience,
        "description": "負責設計與開發高併發後端服務，需具備雲端部署與系統架構設計能力。",
        "is_active": True,
    }
    resp = supabase.table("job_postings").insert(payload).execute()  # upsert → insert
    if not resp.data:
        raise HTTPException(status_code=500, detail="新增失敗")
    return {"message": "測試職缺新增成功", "job_id": resp.data[0]["id"]}


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


def ai_analysis_with_gemini(resume: dict, job: dict) -> dict:
    """呼叫 Gemini API 產生分析結果，回傳格式與原 mock 相同"""

    # ── 資料前處理 ──────────────────────────────────────────
    name          = resume.get("full_name", "求職者")
    education     = resume.get("education", "（未填寫）")
    skills        = resume.get("skills") or []
    experience    = resume.get("experience") or []
    projects      = resume.get("projects") or []
    certifications = resume.get("certifications") or []
    awards        = resume.get("awards") or []
    preferences   = resume.get("preferences") or {}

    job_title       = job.get("title", "目標職位")
    required_skills = job.get("required_skills") or []
    job_desc        = job.get("description", "（未填寫）")
    min_exp         = job.get("min_experience", 0)
    salary_range    = job.get("salary_range", "（未提供）")

    missing_skills = [s for s in required_skills if s not in skills]

    # ── 呼叫 Gemini ─────────────────────────────────────────
    prompt = build_analysis_prompt(
        name, education, skills, experience, projects,
        certifications, awards, preferences,
        job_title, required_skills, job_desc, min_exp, salary_range,
        missing_skills
    )

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw_text = response.text

    return parse_gemini_response(raw_text, missing_skills, job_title)

    # ── 解析 JSON ────────────────────────────────────────────
    return parse_gemini_response(raw_text, missing_skills, job_title)


def build_analysis_prompt(
    name, education, skills, experience, projects,
    certifications, awards, preferences,
    job_title, required_skills, job_desc, min_exp, salary_range,
    missing_skills
) -> str:

    exp_str  = json.dumps(experience,     ensure_ascii=False)
    proj_str = json.dumps(projects,       ensure_ascii=False)
    pref_str = json.dumps(preferences,    ensure_ascii=False)

    return f"""
你是一位資深的人力資源顧問與職涯分析師，專精於台灣軟體業的人才評估。
你的任務是針對一份求職者履歷與一則職缺，產出一份深度分析報告。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【求職者履歷資料】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
姓名：{name}
學歷：{education}
技能：{", ".join(skills) if skills else "（未填寫）"}
工作經歷：{exp_str}
專案作品：{proj_str}
證照：{", ".join(certifications) if certifications else "（無）"}
獎項：{", ".join(awards) if awards else "（無）"}
求職偏好：{pref_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【目標職缺資料】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
職位名稱：{job_title}
必要技能：{", ".join(required_skills) if required_skills else "（未填寫）"}
職位描述：{job_desc}
最低年資要求：{min_exp} 年
薪資範圍：{salary_range}
技能缺口（履歷中缺少的必要技能）：{", ".join(missing_skills) if missing_skills else "無"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【分析任務說明】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
請根據以上資料完成以下四項分析，並以**繁體中文**回答：

1. **情境模擬 (scenario_simulation)**
   - 說明求職者目前的優勢與不足之處
   - 模擬：若補強技能缺口，匹配分數可從現在提升多少（給出具體數字）
   - 包含 SHAP 分析說明：條列每個面向（技能、學歷、年資、專案）對分數的影響
   - 語氣：專業但親切，以「您」稱呼求職者，約 200-300 字

2. **SHAP 權重值 (shap_values)**
   - 計算四個維度對整體評分的貢獻比例
   - 四者加總必須等於 1.0
   - 維度：skill_match（技能匹配）、education（學歷）、experience（工作年資）、projects（專案/作品）
   - 根據實際履歷內容調整比例，不要使用固定值

3. **薪資影響分析 (salary_impact)**
   - 根據目前技能評估市場薪資區間（以台灣市場為準，單位 NT$）
   - 說明補強缺口技能後的薪資成長潛力（%提升幅度）
   - 給出具體數字範圍，約 80-120 字

4. **優先補強技能清單 (priority_skills)**
   - 列出最重要的 3 項待補強技能
   - 每項包含：排名(rank)、技能名稱(skill)、補強理由(reason，約 20-30 字)
   - 優先順序依「對職缺匹配分數的影響程度」排列

5. **整體匹配分數 (match_score)**
   - 0-100 的整數
   - 綜合所有面向評估，60 分以下為不合格，60-75 為尚可，75-90 為良好，90+ 為優秀

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【回傳格式要求（非常重要）】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
你必須**只回傳**以下 JSON 格式，不得包含任何其他文字、說明、markdown 語法或 code fence：

{{
  "scenario_simulation": "（情境模擬全文，字串）",
  "shap_values": {{
    "skill_match": 0.XX,
    "education": 0.XX,
    "experience": 0.XX,
    "projects": 0.XX
  }},
  "salary_impact": "（薪資影響分析全文，字串）",
  "priority_skills": [
    {{"rank": 1, "skill": "技能名稱", "reason": "補強理由"}},
    {{"rank": 2, "skill": "技能名稱", "reason": "補強理由"}},
    {{"rank": 3, "skill": "技能名稱", "reason": "補強理由"}}
  ],
  "match_score": XX
}}
""".strip()


def parse_gemini_response(raw_text: str, missing_skills: list, job_title: str) -> dict:
    """從 Gemini 回傳的文字中萃取 JSON，並做防呆處理"""
    try:
        # 移除 markdown code fence（Gemini 常會包 ```json ... ```）
        clean = re.sub(r"```(?:json)?\s*", "", raw_text).strip().rstrip("`").strip()
        result = json.loads(clean)

        # 確保必要欄位存在，防止 KeyError
        result.setdefault("match_score", 65)
        result.setdefault("scenario_simulation", raw_text)
        result.setdefault("salary_impact", "薪資預估資料不足，請補充更多履歷資訊。")
        result.setdefault("shap_values", {
            "skill_match": 0.45,
            "education": 0.20,
            "experience": 0.25,
            "projects": 0.10
        })
        result.setdefault("priority_skills", [
            {"rank": i+1, "skill": s, "reason": "職缺要求技能，建議優先補強"}
            for i, s in enumerate(missing_skills[:3])
        ])

        # match_score 確保是 int
        result["match_score"] = int(result["match_score"])
        return result

    except (json.JSONDecodeError, ValueError):
        # 萬一 Gemini 沒乖乖回 JSON，降級到基本結構
        return {
            "scenario_simulation": raw_text,
            "shap_values": {"skill_match": 0.45, "education": 0.20,
                            "experience": 0.25, "projects": 0.10},
            "salary_impact": "解析失敗，請重新分析。",
            "priority_skills": [
                {"rank": i+1, "skill": s, "reason": "職缺必要技能"}
                for i, s in enumerate(missing_skills[:3])
            ],
            "match_score": 60,
        }


@app.get("/analyze", tags=["📊 核心功能"])
def analyze_resume():
    # Step 1：取履歷（不變）
    resume_resp = supabase.table("resumes").select("*").order("updated_at", desc=True).limit(1).execute()
    if not resume_resp.data:
        raise HTTPException(status_code=404, detail="找不到履歷")
    resume = resume_resp.data[0]

    # ↓↓↓ Step 2：改為根據 preferences.target_role 選擇職缺 ↓↓↓
    preferences = resume.get("preferences") or {}
    target_role = preferences.get("target_role", "")  # 例如 "後端工程師 / 全端工程師"

    # 取所有開放職缺
    all_jobs_resp = supabase.table("job_postings").select("*").eq("is_active", True).execute()
    all_jobs = all_jobs_resp.data or []

    if not all_jobs:
        raise HTTPException(status_code=404, detail="找不到任何職缺")

    # 用 target_role 做關鍵字比對，找最相關的職缺
    job = match_job_by_role(target_role, all_jobs)

    # Step 3：Mock AI 分析
    try:
        ai_result = ai_analysis_with_gemini(resume, job)
    except Exception as e:
        # Gemini 呼叫失敗時降級回 mock（避免整個 API 掛掉）
        print(f"[WARNING] Gemini API 失敗，降級為 mock: {e}")
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


def match_job_by_role(target_role: str, jobs: list) -> dict:
    """
    根據 target_role 字串從職缺列表中找最相符的一筆。
    比對邏輯：把 target_role 拆成關鍵字，計算每個職缺 title 的命中數。
    """
    if not target_role:
        return jobs[0]  # 沒有目標就回傳第一筆

    # 把 "後端工程師 / 全端工程師" 拆成 ["後端工程師", "全端工程師", "後端", "工程師"]
    keywords = re.split(r"[/／\s、,，]+", target_role)
    keywords = [k.strip() for k in keywords if k.strip()]

    best_job = jobs[0]
    best_score = -1

    for job in jobs:
        title = job.get("title", "")
        score = sum(1 for kw in keywords if kw in title)
        if score > best_score:
            best_score = score
            best_job = job

    return best_job


@app.get("/analysis-results", tags=["📊 核心功能"])
def list_analysis_results():
    """列出所有已儲存的分析結果"""
    response = supabase.table("analysis_results").select("*").order("created_at", desc=True).execute()
    return response.data