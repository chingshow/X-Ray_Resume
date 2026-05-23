# X-Ray Resume

X-Ray Resume 是一個可解釋的履歷分析與職缺匹配決策支援 Web 平台。
平台協助求職者檢視履歷、了解技能缺口與職缺適配度，也可作為企業 / HR 初步理解候選人與職缺需求之間關聯的輔助工具。

---

## 專案結構

```txt
X-Ray_Resume/
├── backend/              # FastAPI 後端
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── schema.sql
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/             # React + Vite 前端
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── main.jsx
│   │   └── XRayResume_JobseekerFrontend.jsx
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── README.md
└── .gitignore
```

---

## 使用技術

### 前端

- React
- Vite
- Tailwind CSS
- lucide-react
- framer-motion

### 後端

- FastAPI
- Uvicorn
- Supabase
- Python

### 資料庫

- Supabase PostgreSQL

---

## 注意事項

請勿將以下檔案或資料夾上傳到 GitHub：

```txt
backend/.env
backend/.venv/
frontend/node_modules/
frontend/dist/
```

`.env` 內含 Supabase 連線資訊，不應公開上傳。

---

## .gitignore 建議內容

```gitignore
# Environment variables
.env
backend/.env

# Python virtual environments
venv/
.venv/
backend/venv/
backend/.venv/

# Python cache
__pycache__/
backend/__pycache__/
**/__pycache__/
*.pyc

# Frontend dependencies and build
frontend/node_modules/
frontend/dist/

# Logs
*.log

# IDE / OS files
.idea/
.DS_Store
```

---

## 後端設定與啟動

### 1. 進入後端資料夾

```bash
cd backend
```

### 2. 建立 Python 環境

如果使用 Conda：

```bash
conda env create -f environment.yml
conda activate webapp
```

如果沒有 Conda，也可以使用 Python venv：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Supabase 環境變數設定

在 `backend/` 資料夾中建立 `.env` 檔案：

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-legacy-anon-public-key
```

注意：

- `SUPABASE_URL` 請使用 Supabase Project URL
- `SUPABASE_URL` 不要包含 `/rest/v1/`
- `SUPABASE_KEY` 請使用 Supabase 的 Legacy anon public key
- `.env` 不要上傳到 GitHub

可以另外提供 `backend/.env.example`：

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-legacy-anon-public-key
```

---

## 啟動後端

```bash
uvicorn app.main:app --reload
```

啟動後開啟：

```txt
http://127.0.0.1:8000/docs
```

可以先測試：

```txt
GET /health
```

如果回傳：

```json
{
  "status": "ok"
}
```

代表後端啟動成功。

---

## 建立 Supabase 資料表

請先到 Supabase SQL Editor 執行 `backend/schema.sql` 內的 SQL，建立資料表。

主要資料表包含：

- profiles
- resumes
- job_postings
- analysis_results
- applications

開發 Demo 階段若遇到 RLS 權限問題，可以先在 Supabase SQL Editor 執行：

```sql
ALTER TABLE public.resumes DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_postings DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_results DISABLE ROW LEVEL SECURITY;
```

正式上線前應重新啟用 RLS 並設定合適的 policies。

---

## 後端測試資料

開啟 Swagger UI：

```txt
http://127.0.0.1:8000/docs
```

依序執行：

```txt
POST /dev/seed-resume
POST /dev/seed-job
GET /analyze
```

如果 `GET /analyze` 回傳分析結果，代表後端與 Supabase 已成功連線。

---

## 前端設定與啟動

### 1. 進入前端資料夾

```bash
cd frontend
```

### 2. 安裝套件

```bash
npm install
```

### 3. 啟動前端

```bash
npm run dev
```

啟動後開啟：

```txt
http://localhost:5173/
```

---

## 前後端串接方式

前端透過 Vite proxy 呼叫後端 API。

`frontend/vite.config.js` 需要包含：

```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
```

前端呼叫：

```txt
/api/analyze
```

會被轉送到：

```txt
http://127.0.0.1:8000/analyze
```

前端呼叫：

```txt
/api/resume
```

會被轉送到：

```txt
http://127.0.0.1:8000/resume
```

---

## Demo 操作流程

### 1. 啟動後端

在第一個 terminal：

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

如果使用 Conda：

```bash
cd backend
conda activate webapp
uvicorn app.main:app --reload
```

---

### 2. 啟動前端

在第二個 terminal：

```bash
cd frontend
npm run dev
```

---

### 3. 建立測試資料

開啟：

```txt
http://127.0.0.1:8000/docs
```

依序執行：

```txt
POST /dev/seed-resume
POST /dev/seed-job
```

---

### 4. 操作前端

開啟：

```txt
http://localhost:5173/
```

操作流程：

```txt
進入平台
→ 求職者入口
→ 檢視履歷 / 修改履歷
→ 儲存變更
→ 查看分析
```

---

## 目前功能

### 求職者端

- 平台首頁
- 求職者工作台
- 檢視目前履歷
- 修改履歷
- 儲存履歷至 Supabase
- 呼叫後端分析 API
- 查看履歷與職缺匹配分析報告
- 顯示技能缺口
- 顯示優先補強技能
- 顯示薪資影響
- 顯示可解釋分析文字

### 後端 API

- `GET /health`
- `POST /resume`
- `POST /dev/seed-resume`
- `POST /dev/seed-job`
- `GET /analyze`

---

## 目前限制

目前分析模型為 Mock AI 分析，並非真正機器學習模型。

目前已完成：

```txt
前端修改履歷
→ 儲存至 Supabase
→ 後端讀取最新履歷
→ 產生分析文字
```

但目前仍有部分限制：

- `match_score` 若尚未改成動態計算，分數可能仍為固定值
- 職缺目前由後端抓取 Supabase 最新一筆 `job_postings`
- HR 端頁面尚未完整實作
- 尚未實作正式登入 / 註冊
- RLS 權限目前可能為開發階段設定

---

## 建議後續開發

### 1. 動態匹配分數

將後端原本固定的 `match_score` 改為根據技能匹配比例計算，例如：

```python
matched_skills = [s for s in required_skills if s in skills]
missing_skills = [s for s in required_skills if s not in skills]

skill_score = len(matched_skills) / len(required_skills) if required_skills else 0
match_score = round(skill_score * 100)
```

### 2. 履歷更新 API

目前前端使用 `POST /resume` 新增履歷。後續可以新增：

```txt
GET /resume/latest
PUT /resume/{resume_id}
```

讓履歷可以被讀取與更新，而不是每次新增一筆。

### 3. HR 端功能

後續可加入：

- 建立職缺
- 管理職缺
- 查看候選人分析
- 候選人排序
- 主動推薦求職者

### 4. 登入與權限

後續可串接 Supabase Auth，區分：

- 求職者
- HR
- 管理者

並重新啟用 RLS policies。

---

## 常見問題

### 1. 後端出現 `supabase_url is required`

代表 `backend/.env` 沒有設定或沒有被正確讀取。請確認：

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-legacy-anon-public-key
```

---

### 2. 後端出現 `Invalid URL`

通常是 `SUPABASE_URL` 格式錯誤。請確認不要使用：

```txt
https://your-project-ref.supabase.co/rest/v1/
```

正確格式是：

```txt
https://your-project-ref.supabase.co
```

---

### 3. 後端出現 RLS 權限錯誤

如果 Demo 階段遇到：

```txt
new row violates row-level security policy
```

可以先在 Supabase SQL Editor 執行：

```sql
ALTER TABLE public.resumes DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_postings DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_results DISABLE ROW LEVEL SECURITY;
```

正式上線前請重新啟用 RLS 並設定 policies。

---

### 4. 前端畫面沒有樣式

請確認前端已安裝 Tailwind：

```bash
npm install tailwindcss @tailwindcss/vite
```

並確認 `frontend/src/index.css` 包含：

```css
@import "tailwindcss";
```

---

### 5. 前端無法呼叫後端

請確認：

1. 後端正在執行：

```txt
http://127.0.0.1:8000
```

2. 前端正在執行：

```txt
http://localhost:5173
```

3. `vite.config.js` 有設定 `/api` proxy。

---

## 開發狀態

目前專案為課程 / Demo 階段版本。

核心重點為：

- 可解釋履歷分析
- 職缺匹配決策支援
- 技能缺口提示
- 前後端 API 串接
- Supabase 資料儲存
