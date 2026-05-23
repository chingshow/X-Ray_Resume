import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. 載入環境變數
load_dotenv()

# 2. 初始化 FastAPI
app = FastAPI(title="X-Ray Resume API")

# 3. 初始化 Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


# --- 2. 完美對接 SQL 的 Pydantic 模型 ---

class ResumeCreate(BaseModel):
    user_id: str                      # 對應 profiles(id)
    full_name: Optional[str] = None   # 姓名
    education: Optional[str] = None   # 學歷
    experience: Optional[List[Dict[str, Any]]] = None  # 工作經歷 (jsonb)
    skills: Optional[List[str]] = None                 # 技能關鍵詞 (text[])
    projects: Optional[List[Dict[str, Any]]] = None    # 專案作品連結 (jsonb)
    certifications: Optional[List[str]] = None         # 證照 (text[])
    awards: Optional[List[str]] = None                 # 獎項 (text[])
    completion_rate: Optional[int] = 0                 # 整體完成度
    preferences: Optional[Dict[str, Any]] = None       # 求職條件 (jsonb)


# --- API 路由 ---

@app.get("/")
def read_root():
    return {"message": "X-Ray Resume Backend is running!"}

# 實作精準對接的 POST /resume API
@app.post("/resume", status_code=status.HTTP_201_CREATED)
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