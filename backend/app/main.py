import os
from fastapi import FastAPI
from dotenv import load_dotenv
from supabase import create_client, Client

# 載入環境變數
load_dotenv()

app = FastAPI(title="My App", version="0.1.0")

# 初始化 Supabase 客戶端
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


@app.get("/")
def read_root():
    return {"message": "X-Ray Resume Backend is running!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# 測試讀取資料表的 API (以 profiles 為例)
@app.get("/test-db")
def test_db():
    response = supabase.table("profiles").select("*").execute()
    return response.data

