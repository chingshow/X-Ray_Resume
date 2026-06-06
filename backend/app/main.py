import os
import re
import json
import math
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, status, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai

load_dotenv()

app = FastAPI(title="X-Ray Resume API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SESSION_TTL_HOURS = 24


# ===========================================================================
# Pydantic Models
# ===========================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class ResumeUpsert(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None          # "male" | "female" | "undisclosed"
    education: Optional[str] = None
    experience: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    awards: Optional[List[str]] = None
    completion_rate: Optional[int] = 0
    preferences: Optional[Dict[str, Any]] = None


class JobCreate(BaseModel):
    title: str
    company: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = []
    salary_range: Optional[str] = None
    min_experience: Optional[int] = 0


class ApplicationCreate(BaseModel):
    job_id: str


class HRDecision(BaseModel):
    decision: str           # "selected" | "rejected"
    hr_reply: Optional[str] = ""


class FavoriteToggle(BaseModel):
    job_id: str


# ===========================================================================
# Auth helpers
# ===========================================================================

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token() -> str:
    return secrets.token_urlsafe(48)


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """
    Dependency: validates Bearer token from Authorization header.
    Returns the user row dict on success, raises 401 on failure.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供有效的 Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    now = datetime.now(timezone.utc).isoformat()

    try:
        resp = (
            supabase.table("sessions")
            .select("*, users(*)")
            .eq("token", token)
            .gt("expires_at", now)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session 查詢失敗: {str(e)}")

    if not resp.data:
        raise HTTPException(status_code=401, detail="Token 無效或已過期，請重新登入")

    return resp.data[0]["users"]


def require_role(role: str):
    """Factory: returns a dependency that enforces a specific role."""
    def _check(user: Dict = Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(status_code=403, detail=f"此操作需要 {role} 權限")
        return user
    return _check


# ===========================================================================
# Basic routes
# ===========================================================================

@app.get("/")
def read_root():
    return {"message": "X-Ray Resume API v1.0.0 is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ===========================================================================
# Auth routes
# ===========================================================================

@app.post("/auth/login", tags=["🔐 Auth"])
def login(body: LoginRequest):
    """Login with username + password, returns session token and user info."""
    pw_hash = _hash_password(body.password)

    try:
        resp = (
            supabase.table("users")
            .select("*")
            .eq("username", body.username.strip())
            .eq("password_hash", pw_hash)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"資料庫查詢失敗: {str(e)}")

    if not resp.data:
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")

    user = resp.data[0]
    token = _generate_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)).isoformat()

    try:
        supabase.table("sessions").insert({
            "token": token,
            "user_id": user["id"],
            "expires_at": expires_at,
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立 Session 失敗: {str(e)}")

    return {
        "token": token,
        "expires_at": expires_at,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
        },
    }


@app.post("/auth/logout", tags=["🔐 Auth"])
def logout(authorization: Optional[str] = Header(None)):
    """Invalidate the current session token."""
    if not authorization or not authorization.startswith("Bearer "):
        return {"message": "已登出"}

    token = authorization.split(" ", 1)[1].strip()
    try:
        supabase.table("sessions").delete().eq("token", token).execute()
    except Exception:
        pass

    return {"message": "已成功登出"}


# ===========================================================================
# Resume routes
# ===========================================================================

@app.post("/resume", tags=["📄 履歷"], status_code=200)
def upsert_resume(
    body: ResumeUpsert,
    user: Dict = Depends(get_current_user),
):
    """Create or update the current user's resume (one per user, upsert by user_id)."""
    if user.get("role") != "jobseeker":
        raise HTTPException(status_code=403, detail="只有求職者可以上傳履歷")

    data = body.model_dump(exclude_unset=True)
    data["user_id"] = user["id"]
    data["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        # Check if resume already exists for this user
        existing = (
            supabase.table("resumes")
            .select("id")
            .eq("user_id", user["id"])
            .limit(1)
            .execute()
        )

        if existing.data:
            # Update existing
            resp = (
                supabase.table("resumes")
                .update(data)
                .eq("user_id", user["id"])
                .execute()
            )
        else:
            # Insert new
            resp = supabase.table("resumes").insert(data).execute()

        if not resp.data:
            raise HTTPException(status_code=400, detail="儲存履歷失敗")

        return {"message": "履歷已儲存", "data": resp.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"伺服器錯誤: {str(e)}")


@app.get("/resume/me", tags=["📄 履歷"])
def get_my_resume(user: Dict = Depends(get_current_user)):
    """Get the current jobseeker's resume."""
    if user.get("role") != "jobseeker":
        raise HTTPException(status_code=403, detail="只有求職者可以查看此資源")

    try:
        resp = (
            supabase.table("resumes")
            .select("*")
            .eq("user_id", user["id"])
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

    if not resp.data:
        return {"data": None, "message": "尚未建立履歷"}

    return {"data": resp.data[0]}


# ===========================================================================
# Analysis route
# ===========================================================================

@app.get("/analyze", tags=["📊 分析"])
def analyze_resume(user: Dict = Depends(get_current_user)):
    """Run AI analysis on the current user's resume against the best matching job."""
    if user.get("role") != "jobseeker":
        raise HTTPException(status_code=403, detail="只有求職者可以執行分析")

    # 1. Fetch this user's resume
    try:
        resume_resp = (
            supabase.table("resumes")
            .select("*")
            .eq("user_id", user["id"])
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得履歷失敗: {str(e)}")

    if not resume_resp.data:
        raise HTTPException(status_code=404, detail="請先填寫並儲存履歷再執行分析")

    resume = resume_resp.data[0]

    # 2. Find best matching job based on target_role preference
    try:
        jobs_resp = (
            supabase.table("job_postings")
            .select("*")
            .eq("is_active", True)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得職缺失敗: {str(e)}")

    all_jobs = jobs_resp.data or []
    if not all_jobs:
        raise HTTPException(status_code=404, detail="目前沒有開放職缺，請請 HR 先新增職缺")

    preferences = resume.get("preferences") or {}
    target_role = preferences.get("target_role", "")
    job = _match_job_by_role(target_role, all_jobs)

    # 3. Check cache: if analysis exists and resume hasn't been updated since, return it directly
    resume_updated_at = resume.get("updated_at") or resume.get("created_at")
    try:
        cached_resp = (
            supabase.table("analysis_results")
            .select("*")
            .eq("resume_id", resume["id"])
            .eq("job_id", job["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        cached = cached_resp.data[0] if cached_resp.data else None
    except Exception:
        cached = None

    if cached and resume_updated_at:
        analysis_created_at = cached.get("created_at")
        if analysis_created_at:
            from datetime import datetime as _dt
            try:
                def _parse(ts):
                    return _dt.fromisoformat(str(ts).replace("Z", "+00:00"))
                if _parse(analysis_created_at) >= _parse(resume_updated_at):
                    # Return cached result without calling AI
                    return {
                        "cached": True,
                        "analysis_id": cached["id"],
                        "resume_snapshot": {
                            "full_name": resume.get("full_name"),
                            "education": resume.get("education"),
                            "skills": resume.get("skills"),
                        },
                        "job_snapshot": {
                            "job_id": job.get("id"),
                            "title": job.get("title"),
                            "required_skills": job.get("required_skills"),
                        },
                        "match_score": cached.get("match_score"),
                        "shap_values": cached.get("shap_values") or {},
                        "scenario_simulation": cached.get("explanation") or "",
                        "salary_impact": "",
                        "priority_skills": cached.get("priority_skills") or [],
                        "skill_gaps": cached.get("skill_gaps") or [],
                    }
            except Exception as e:
                print(f"[WARNING] 快取時間比較失敗，重新分析: {e}")

    # 4. AI analysis (cache miss or resume updated)
    try:
        ai_result = _ai_analysis_with_gemini(resume, job)
    except Exception as e:
        print(f"[WARNING] Gemini API 失敗，降級為 mock: {e}")
        ai_result = _mock_ai_analysis(resume, job)

    # 4. Save analysis result (upsert by resume_id + job_id)
    #    Also look up the application_id so HR can JOIN directly.
    application_id = None
    try:
        app_resp = (
            supabase.table("applications")
            .select("id")
            .eq("resume_id", resume["id"])
            .eq("job_id", job["id"])
            .limit(1)
            .execute()
        )
        if app_resp.data:
            application_id = app_resp.data[0]["id"]
    except Exception as e:
        print(f"[WARNING] 查詢 application_id 失敗: {e}")

    analysis_payload = {
        "resume_id": resume["id"],
        "job_id": job["id"],
        "match_score": ai_result["match_score"],
        "skill_gaps": [p["skill"] for p in ai_result["priority_skills"]],
        "explanation": ai_result["scenario_simulation"],
        "shap_values": ai_result["shap_values"],
        "salary_impact": ai_result["salary_impact"],
        "priority_skills": ai_result["priority_skills"],
    }
    if application_id:
        analysis_payload["application_id"] = application_id

    try:
        existing_analysis = (
            supabase.table("analysis_results")
            .select("id")
            .eq("resume_id", resume["id"])
            .eq("job_id", job["id"])
            .limit(1)
            .execute()
        )
        if existing_analysis.data:
            save_resp = (
                supabase.table("analysis_results")
                .update(analysis_payload)
                .eq("id", existing_analysis.data[0]["id"])
                .execute()
            )
        else:
            save_resp = (
                supabase.table("analysis_results")
                .insert(analysis_payload)
                .execute()
            )
    except Exception as e:
        print(f"[WARNING] 儲存分析結果失敗: {e}")
        save_resp = type("R", (), {"data": [{"id": None}]})()

    analysis_id = save_resp.data[0]["id"] if save_resp.data else None

    return {
        "analysis_id": analysis_id,
        "resume_snapshot": {
            "full_name": resume.get("full_name"),
            "education": resume.get("education"),
            "skills": resume.get("skills"),
        },
        "job_snapshot": {
            "job_id": job.get("id"),
            "title": job.get("title"),
            "required_skills": job.get("required_skills"),
        },
        **ai_result,
    }


@app.get("/analysis-results", tags=["📊 分析"])
def list_analysis_results(user: Dict = Depends(get_current_user)):
    """
    Jobseeker: returns their own analysis results.
    HR: returns all analysis results (for candidate review).
    """
    try:
        if user["role"] == "jobseeker":
            resume_resp = (
                supabase.table("resumes")
                .select("id")
                .eq("user_id", user["id"])
                .limit(1)
                .execute()
            )
            if not resume_resp.data:
                return []
            resume_id = resume_resp.data[0]["id"]
            resp = (
                supabase.table("analysis_results")
                .select("*")
                .eq("resume_id", resume_id)
                .order("created_at", desc=True)
                .execute()
            )
        else:
            resp = (
                supabase.table("analysis_results")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
        return resp.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


# ===========================================================================
# Job routes
# ===========================================================================

@app.get("/jobs", tags=["💼 職缺"])
def list_jobs(_: Dict = Depends(get_current_user)):
    """List all active job postings (accessible to all logged-in users)."""
    try:
        resp = (
            supabase.table("job_postings")
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


@app.post("/jobs", tags=["💼 職缺"], status_code=201)
def create_job(
    body: JobCreate,
    user: Dict = Depends(require_role("hr")),
):
    """HR creates a new job posting."""
    payload = {
        "title": body.title,
        "company": body.company,
        "description": body.description,
        "required_skills": body.required_skills or [],
        "salary_range": body.salary_range,
        "min_experience": body.min_experience or 0,
        "is_active": True,
        "created_by": user["id"],
    }
    try:
        resp = supabase.table("job_postings").insert(payload).execute()
        if not resp.data:
            raise HTTPException(status_code=400, detail="新增職缺失敗")
        return {"message": "職缺已建立", "data": resp.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"伺服器錯誤: {str(e)}")


@app.get("/jobs/my", tags=["💼 職缺"])
def list_my_jobs(user: Dict = Depends(require_role("hr"))):
    """HR: list all jobs created by this HR account, with application_count per job."""
    try:
        resp = (
            supabase.table("job_postings")
            .select("*")
            .eq("created_by", user["id"])
            .order("created_at", desc=True)
            .execute()
        )
        jobs = resp.data or []

        if not jobs:
            return []

        # Fetch application counts for all jobs in one query
        job_ids = [job["id"] for job in jobs]
        apps_resp = (
            supabase.table("applications")
            .select("job_id")
            .in_("job_id", job_ids)
            .execute()
        )
        apps_data = apps_resp.data or []

        # Count applications per job_id
        count_map: Dict[str, int] = {}
        for app in apps_data:
            jid = app["job_id"]
            count_map[jid] = count_map.get(jid, 0) + 1

        # Attach application_count to each job
        for job in jobs:
            job["application_count"] = count_map.get(job["id"], 0)

        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


@app.get("/jobs/{job_id}/applications", tags=["💼 職缺"])
def get_job_applications(
    job_id: str,
    user: Dict = Depends(require_role("hr")),
):
    """HR: get all applications for a specific job with resume and analysis info."""
    try:
        # Step 1: fetch applications with resume + user info
        apps_resp = (
            supabase.table("applications")
            .select("*, resumes(*, users(display_name, username))")
            .eq("job_id", job_id)
            .order("created_at", desc=True)
            .execute()
        )
        apps = apps_resp.data or []

        if not apps:
            return []

        # Step 2: fetch analysis_results for this job in one query,
        # keyed by application_id (preferred) or resume_id (fallback)
        resume_ids = [a["resume_id"] for a in apps if a.get("resume_id")]
        analysis_resp = (
            supabase.table("analysis_results")
            .select("*")
            .eq("job_id", job_id)
            .in_("resume_id", resume_ids)
            .execute()
        )
        analysis_list = analysis_resp.data or []

        # Build lookup maps
        analysis_by_app_id: Dict[str, dict] = {}
        analysis_by_resume_id: Dict[str, dict] = {}
        for ar in analysis_list:
            if ar.get("application_id"):
                analysis_by_app_id[ar["application_id"]] = ar
            if ar.get("resume_id"):
                analysis_by_resume_id[ar["resume_id"]] = ar

        # Step 3: merge
        for app in apps:
            ar = (
                analysis_by_app_id.get(app["id"])
                or analysis_by_resume_id.get(app.get("resume_id"))
            )
            app["analysis_results"] = [ar] if ar else []

        return apps
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


# ===========================================================================
# Application routes
# ===========================================================================

@app.post("/applications", tags=["📨 投遞"], status_code=201)
def apply_to_job(
    body: ApplicationCreate,
    user: Dict = Depends(require_role("jobseeker")),
):
    """Jobseeker applies to a job posting."""
    # Check resume exists
    try:
        resume_resp = (
            supabase.table("resumes")
            .select("id")
            .eq("user_id", user["id"])
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢履歷失敗: {str(e)}")

    if not resume_resp.data:
        raise HTTPException(status_code=400, detail="請先填寫並儲存履歷才能投遞")

    resume_id = resume_resp.data[0]["id"]

    # Check job exists
    try:
        job_resp = (
            supabase.table("job_postings")
            .select("id, title")
            .eq("id", body.job_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢職缺失敗: {str(e)}")

    if not job_resp.data:
        raise HTTPException(status_code=404, detail="職缺不存在或已關閉")

    # Check duplicate application
    try:
        dup = (
            supabase.table("applications")
            .select("id")
            .eq("user_id", user["id"])
            .eq("job_id", body.job_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

    if dup.data:
        raise HTTPException(status_code=409, detail="你已經投遞過這個職缺")

    # Create application
    payload = {
        "user_id": user["id"],
        "resume_id": resume_id,
        "job_id": body.job_id,
        "status": "pending",
        "hr_decision": None,
        "hr_reply": "",
    }
    try:
        resp = supabase.table("applications").insert(payload).execute()
        if not resp.data:
            raise HTTPException(status_code=400, detail="投遞失敗")
        return {"message": "投遞成功", "data": resp.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"伺服器錯誤: {str(e)}")


@app.get("/applications/my", tags=["📨 投遞"])
def get_my_applications(user: Dict = Depends(require_role("jobseeker"))):
    """Jobseeker: get all their applications with job info and HR reply."""
    try:
        resp = (
            supabase.table("applications")
            .select("*, job_postings(title, company, salary_range, required_skills)")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


@app.put("/applications/{application_id}/decision", tags=["📨 投遞"])
def update_application_decision(
    application_id: str,
    body: HRDecision,
    user: Dict = Depends(require_role("hr")),
):
    """HR: set decision (selected/rejected) and optional reply for an application."""
    if body.decision not in ("selected", "rejected"):
        raise HTTPException(status_code=400, detail="decision 必須是 selected 或 rejected")

    status_map = {"selected": "selected", "rejected": "rejected"}

    try:
        resp = (
            supabase.table("applications")
            .update({
                "hr_decision": body.decision,
                "hr_reply": body.hr_reply or "",
                "status": status_map[body.decision],
            })
            .eq("id", application_id)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="找不到此投遞紀錄")
        return {"message": "決定已更新", "data": resp.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失敗: {str(e)}")


# ===========================================================================
# Favorites routes
# ===========================================================================

@app.post("/favorites", tags=["⭐ 收藏"], status_code=200)
def toggle_favorite(
    body: FavoriteToggle,
    user: Dict = Depends(require_role("jobseeker")),
):
    """Toggle favorite status for a job. Returns current favorites list."""
    try:
        user_resp = (
            supabase.table("users")
            .select("favorite_job_ids")
            .eq("id", user["id"])
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

    favorites: List[str] = user_resp.data[0].get("favorite_job_ids") or []

    if body.job_id in favorites:
        favorites.remove(body.job_id)
        action = "removed"
    else:
        favorites.append(body.job_id)
        action = "added"

    try:
        supabase.table("users").update({"favorite_job_ids": favorites}).eq("id", user["id"]).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新收藏失敗: {str(e)}")

    return {"action": action, "favorite_job_ids": favorites}


@app.get("/favorites", tags=["⭐ 收藏"])
def get_favorites(user: Dict = Depends(require_role("jobseeker"))):
    """Get the current user's list of favorite job IDs."""
    try:
        user_resp = (
            supabase.table("users")
            .select("favorite_job_ids")
            .eq("id", user["id"])
            .limit(1)
            .execute()
        )
        favorites = user_resp.data[0].get("favorite_job_ids") or []
        return {"favorite_job_ids": favorites}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


# ===========================================================================
# AI helpers (unchanged logic, now properly scoped)
# ===========================================================================

def _mock_ai_analysis(resume: dict, job: dict) -> dict:
    import random
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
        "shap_values": {"skill_match": 0.45, "education": 0.20, "experience": 0.25, "projects": 0.10},
        "salary_impact": (
            f"目前以您的技能組合（{skills_str}）在市場上預估年薪範圍約 NT$600,000 – NT$800,000。\n"
            f"若補強「{missing_str}」後，預估可提升至 NT$850,000 – NT$1,100,000（+25%）。"
        ),
        "priority_skills": [
            {"rank": 1, "skill": missing_skills[0] if len(missing_skills) > 0 else "雲端架構", "reason": "職缺必要技能，缺少影響分數最大"},
            {"rank": 2, "skill": missing_skills[1] if len(missing_skills) > 1 else "系統設計", "reason": "加分項目，可顯著提升競爭力"},
            {"rank": 3, "skill": missing_skills[2] if len(missing_skills) > 2 else "英文能力", "reason": "跨國職缺加分，長期職涯必備"},
        ],
        "match_score": random.randint(60, 85),
    }


def _ai_analysis_with_gemini(resume: dict, job: dict) -> dict:
    name = resume.get("full_name", "求職者")
    gender = resume.get("gender", "")
    education = resume.get("education", "（未填寫）")
    skills = resume.get("skills") or []
    experience = resume.get("experience") or []
    projects = resume.get("projects") or []
    certifications = resume.get("certifications") or []
    awards = resume.get("awards") or []
    preferences = resume.get("preferences") or {}

    job_title = job.get("title", "目標職位")
    required_skills = job.get("required_skills") or []
    job_desc = job.get("description", "（未填寫）")
    min_exp = job.get("min_experience", 0)
    salary_range = job.get("salary_range", "（未提供）")
    missing_skills = [s for s in required_skills if s not in skills]

    prompt = _build_analysis_prompt(
        name, gender, education, skills, experience, projects,
        certifications, awards, preferences,
        job_title, required_skills, job_desc, min_exp, salary_range, missing_skills,
    )

    response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return _parse_gemini_response(response.text, missing_skills, job_title)


def _build_analysis_prompt(
    name, gender, education, skills, experience, projects,
    certifications, awards, preferences,
    job_title, required_skills, job_desc, min_exp, salary_range, missing_skills,
) -> str:
    return f"""
你是一位資深人力資源顧問、職涯教練與履歷分析師，熟悉台灣職場、軟體產業與新鮮人/轉職者求職情境。

你的任務不是批評求職者，而是用「專業、溫暖、具體、可行動」的方式，幫助求職者理解：
1. 自己目前和目標職缺的契合程度
2. 目前履歷中最有價值的亮點
3. 影響錄取機率的主要缺口
4. 下一步最值得補強的技能與行動方向
5. 這些補強可能對薪資與面試機會造成什麼影響

請避免使用冷冰冰、制式化、過度誇張或打擊人的語氣。
請不要說「你不適合」，而是改成「目前若補強哪些項目，會更接近此職缺期待」。
請根據提供的資料分析，不要編造不存在的經歷、證照、公司或學校。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【求職者履歷資料】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
姓名：{name}
性別：{gender}
學歷：{education}
技能：{", ".join(skills) if skills else "（未填寫）"}
工作經歷：{json.dumps(experience, ensure_ascii=False)}
專案作品：{json.dumps(projects, ensure_ascii=False)}
證照：{", ".join(certifications) if certifications else "（無）"}
獎項：{", ".join(awards) if awards else "（無）"}
求職偏好：{json.dumps(preferences, ensure_ascii=False)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【目標職缺資料】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
職位名稱：{job_title}
必要技能：{", ".join(required_skills) if required_skills else "（未填寫）"}
職位描述：{job_desc}
最低年資要求：{min_exp} 年
薪資範圍：{salary_range}
技能缺口：{", ".join(missing_skills) if missing_skills else "無"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【分析規則】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

請根據以下標準進行分析：

一、match_score 評分規則，請回傳 0 到 100 的整數（打分數標準必須使用 SHAP 量化概念，總分評估需嚴格對應並反映下方各項特徵的貢獻權重）：
- 90-100：高度契合，履歷與職缺需求非常接近
- 75-89：具備良好競爭力，但仍有少數可補強處
- 60-74：有基本潛力，但需要補強關鍵技能或經驗
- 40-59：部分條件符合，但與職缺期待仍有明顯落差
- 0-39：目前資料不足或職缺落差較大

二、shap_values 規則：
請用 0 到 1 的小數表示各因素對匹配結果的影響權重。
四個數值總和必須接近 1.0。
- skill_match：技能與職缺必要技能的符合程度
- education：學歷與職缺背景的關聯性
- experience：工作經驗與最低年資/職務內容的符合程度
- projects：專案作品與職缺任務的相關性

三、priority_skills 規則：
請優先從「技能缺口」中挑選。
如果沒有明顯技能缺口，請根據職缺描述與求職者目前技能，提出最值得強化的進階能力。
每個 reason 必須具體說明為什麼這個技能會提升匹配度。

四、scenario_simulation 規則：
請寫成一段自然、鼓勵式的職涯分析。
內容必須包含：
- 求職者目前的優勢
- 與目標職缺的落差
- 如果補強優先技能，可能帶來的改變
- 對面試或錄取機會的實際幫助

五、salary_impact 規則：
請根據職缺薪資範圍與技能缺口，用保守語氣分析。
不要保證加薪。
請使用「可能」、「有機會」、「通常會提升」等語氣。
如果薪資資料不足，請明確說明資料不足，但仍可分析技能補強對談薪的幫助。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【分析任務】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
請以繁體中文完成以下分析，只回傳 JSON，不得包含任何其他文字或 markdown：

{{
  "scenario_simulation": "情境模擬全文（200-300字）",
  "shap_values": {{"skill_match": 0.XX, "education": 0.XX, "experience": 0.XX, "projects": 0.XX}},
  "salary_impact": "薪資影響分析（80-120字）",
  "priority_skills": [
    {{"rank": 1, "skill": "技能名稱", "reason": "補強理由"}},
    {{"rank": 2, "skill": "技能名稱", "reason": "補強理由"}},
    {{"rank": 3, "skill": "技能名稱", "reason": "補強理由"}}
  ],
  "match_score": XX
}}
""".strip()


def _parse_gemini_response(raw_text: str, missing_skills: list, job_title: str) -> dict:
    try:
        clean = re.sub(r"```(?:json)?\s*", "", raw_text).strip().rstrip("`").strip()
        result = json.loads(clean)
        result.setdefault("match_score", 65)
        result.setdefault("scenario_simulation", raw_text)
        result.setdefault("salary_impact", "薪資預估資料不足，請補充更多履歷資訊。")
        result.setdefault("shap_values", {"skill_match": 0.45, "education": 0.20, "experience": 0.25, "projects": 0.10})
        result.setdefault("priority_skills", [
            {"rank": i + 1, "skill": s, "reason": "職缺要求技能，建議優先補強"}
            for i, s in enumerate(missing_skills[:3])
        ])
        result["match_score"] = int(result["match_score"])
        return result
    except (json.JSONDecodeError, ValueError):
        return {
            "scenario_simulation": raw_text,
            "shap_values": {"skill_match": 0.45, "education": 0.20, "experience": 0.25, "projects": 0.10},
            "salary_impact": "解析失敗，請重新分析。",
            "priority_skills": [{"rank": i + 1, "skill": s, "reason": "職缺必要技能"} for i, s in enumerate(missing_skills[:3])],
            "match_score": 60,
        }


def _match_job_by_role(target_role: str, jobs: list) -> dict:
    if not target_role:
        return jobs[0]
    keywords = re.split(r"[/／\s、,，]+", target_role)
    keywords = [k.strip() for k in keywords if k.strip()]
    best_job, best_score = jobs[0], -1
    for job in jobs:
        score = sum(1 for kw in keywords if kw in job.get("title", ""))
        if score > best_score:
            best_score, best_job = score, job
    return best_job

# ===========================================================================
# Register route  (需求1：SHA-256 密碼)
# ===========================================================================

class RegisterRequest(BaseModel):
    display_name: str
    username: str
    password: str
    role: Optional[str] = "jobseeker"   # "jobseeker" | "hr"


@app.post("/auth/register", tags=["🔐 Auth"], status_code=201)
def register(body: RegisterRequest):
    """
    Register a new user.
    Password is stored as SHA-256 hash — consistent with the login flow.
    """
    if body.role not in ("jobseeker", "hr"):
        raise HTTPException(status_code=400, detail="role 必須是 jobseeker 或 hr")

    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="使用者名稱不能為空")

    # Check duplicate username
    try:
        dup = (
            supabase.table("users")
            .select("id")
            .eq("username", username)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"資料庫查詢失敗: {str(e)}")

    if dup.data:
        raise HTTPException(status_code=409, detail="此使用者名稱已被使用，請換一個")

    pw_hash = _hash_password(body.password)

    try:
        resp = supabase.table("users").insert({
            "username": username,
            "display_name": body.display_name.strip() or username,
            "password_hash": pw_hash,
            "role": body.role,
        }).execute()
        if not resp.data:
            raise HTTPException(status_code=400, detail="建立帳號失敗")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"伺服器錯誤: {str(e)}")

    user = resp.data[0]
    return {
        "message": "帳號建立成功",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
        },
    }


# ===========================================================================
# Job-specific analysis route  (需求3：針對特定職缺進行分析)
# ===========================================================================

@app.post("/analyze/job/{job_id}", tags=["📊 分析"])
def analyze_resume_for_job(
    job_id: str,
    user: Dict = Depends(get_current_user),
):
    """
    Run AI analysis for the current user's resume against a specific job posting.
    - If an analysis already exists and the resume has NOT been updated since, return the cached result.
    - Otherwise, run a fresh AI analysis and upsert the result.
    """
    if user.get("role") != "jobseeker":
        raise HTTPException(status_code=403, detail="只有求職者可以執行分析")

    # 1. Fetch resume
    try:
        resume_resp = (
            supabase.table("resumes")
            .select("*")
            .eq("user_id", user["id"])
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得履歷失敗: {str(e)}")

    if not resume_resp.data:
        raise HTTPException(status_code=404, detail="請先填寫並儲存履歷再執行分析")

    resume = resume_resp.data[0]

    # 2. Fetch the target job
    try:
        job_resp = (
            supabase.table("job_postings")
            .select("*")
            .eq("id", job_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得職缺失敗: {str(e)}")

    if not job_resp.data:
        raise HTTPException(status_code=404, detail="職缺不存在或已關閉")

    job = job_resp.data[0]

    # 3. Check if a cached analysis exists and is still valid
    #    (i.e., analysis was created AFTER the resume was last updated)
    try:
        existing_resp = (
            supabase.table("analysis_results")
            .select("*")
            .eq("resume_id", resume["id"])
            .eq("job_id", job_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as e:
        existing_resp = type("R", (), {"data": []})()

    cached = existing_resp.data[0] if existing_resp.data else None
    resume_updated_at = resume.get("updated_at") or resume.get("created_at")

    if cached:
        # 優先抓取分析結果最後更新的時間，如果沒有才用建立時間
        analysis_time = cached.get("updated_at") or cached.get("created_at")
        # Return cache when analysis is newer than the last resume update
        if resume_updated_at and analysis_time:
            from datetime import datetime
            try:
                # Normalize both timestamps for comparison
                def _parse_ts(ts):
                    ts = str(ts).replace("Z", "+00:00")
                    return datetime.fromisoformat(ts)

                if _parse_ts(analysis_time) >= _parse_ts(resume_updated_at):
                    return {
                        "cached": True,
                        "analysis_id": cached["id"],
                        "resume_snapshot": {
                            "full_name": resume.get("full_name"),
                            "education": resume.get("education"),
                            "skills": resume.get("skills"),
                        },
                        "job_snapshot": {
                            "job_id": job.get("id"),
                            "title": job.get("title"),
                            "required_skills": job.get("required_skills"),
                        },
                        "match_score": cached.get("match_score"),
                        "shap_values": cached.get("shap_values"),
                        "scenario_simulation": cached.get("explanation"),
                        "salary_impact": None,
                        "priority_skills": cached.get("priority_skills") or [],
                        "skill_gaps": cached.get("skill_gaps") or [],
                    }
            except Exception as e:
                print(f"[WARNING] 時間戳比較失敗，將重新分析: {e}")

    # 4. Run fresh AI analysis
    try:
        ai_result = _ai_analysis_with_gemini(resume, job)
    except Exception as e:
        print(f"[WARNING] Gemini API 失敗，降級為 mock: {e}")
        ai_result = _mock_ai_analysis(resume, job)

    # 5. Look up application_id (if applied)
    application_id = None
    try:
        app_resp = (
            supabase.table("applications")
            .select("id")
            .eq("resume_id", resume["id"])
            .eq("job_id", job_id)
            .limit(1)
            .execute()
        )
        if app_resp.data:
            application_id = app_resp.data[0]["id"]
    except Exception as e:
        print(f"[WARNING] 查詢 application_id 失敗: {e}")

    # 6. Upsert analysis result
    analysis_payload = {
        "resume_id": resume["id"],
        "job_id": job_id,
        "match_score": ai_result["match_score"],
        "skill_gaps": [p["skill"] for p in ai_result["priority_skills"]],
        "explanation": ai_result["scenario_simulation"],
        "shap_values": ai_result["shap_values"],
        "salary_impact": ai_result["salary_impact"],
        "priority_skills": ai_result["priority_skills"],
    }
    if application_id:
        analysis_payload["application_id"] = application_id

    try:
        if cached:
            save_resp = (
                supabase.table("analysis_results")
                .update(analysis_payload)
                .eq("id", cached["id"])
                .execute()
            )
        else:
            save_resp = (
                supabase.table("analysis_results")
                .insert(analysis_payload)
                .execute()
            )
    except Exception as e:
        print(f"[WARNING] 儲存分析結果失敗: {e}")
        save_resp = type("R", (), {"data": [{"id": None}]})()

    analysis_id = save_resp.data[0]["id"] if save_resp.data else None

    return {
        "cached": False,
        "analysis_id": analysis_id,
        "resume_snapshot": {
            "full_name": resume.get("full_name"),
            "education": resume.get("education"),
            "skills": resume.get("skills"),
        },
        "job_snapshot": {
            "job_id": job.get("id"),
            "title": job.get("title"),
            "required_skills": job.get("required_skills"),
        },
        **ai_result,
    }
