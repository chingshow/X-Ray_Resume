# X-Ray Resume

X-Ray Resume 是一個可解釋的履歷分析與職缺匹配決策支援 Web 平台。

平台協助求職者檢視履歷、了解技能缺口與職缺適配度，也可作為企業 / HR 初步理解候選人與職缺需求之間關聯的輔助工具。

---

## 專案結構

```txt
X-Ray_Resume/
├── backend/                              # FastAPI 後端
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py                       # 後端主程式，包含 Auth、Resume、Jobs、Applications、Favorites、AI Analysis API
│   │
│   ├── schema.sql                        # Supabase PostgreSQL 資料表結構與欄位設定
│   ├── requirements.txt                  # Python 套件需求
│   ├── environment.yml                   # Conda 環境設定，若使用 Conda 可用
│   ├── .env.example                      # 環境變數範例
│   └── .env                              # 本機環境變數，實際開發使用，不上傳 GitHub
│
├── frontend/                             # React + Vite 前端
│   ├── public/                           # 靜態資源
│   │
│   ├── src/
│   │   ├── App.jsx                       # 前端入口元件
│   │   ├── main.jsx                      # React 掛載入口
│   │   ├── index.css                     # Tailwind CSS 與全域樣式
│   │   └── XRayResume_JobseekerFrontend.jsx
│   │                                      # 主要前端頁面，包含求職者端、HR 端、登入、註冊、履歷、職缺、投遞與分析介面
│   │
│   ├── index.html                        # Vite HTML 入口
│   ├── package.json                      # 前端套件與 scripts
│   ├── package-lock.json                 # npm 套件鎖定檔
│   └── vite.config.js                    # Vite 設定與 API proxy
│
├── README.md                             # 專案說明文件
└── .gitignore                            # Git 忽略檔案設定
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
- Supabase Python Client
- Google GenAI

### 資料庫

- Supabase PostgreSQL

### AI 分析

- Gemini API
- 結構化 Prompt
- 類 SHAP 四維度權重解釋

---

## 核心功能

### 求職者端

- 求職者登入 / 註冊
- 角色入口限制
- 檢視履歷
- 修改履歷
- 儲存履歷至 Supabase
- 履歷必填欄位檢查
- 姓名依帳號資料帶入，不開放在履歷頁修改
- 呼叫 AI 分析 API
- 查看履歷與職缺匹配分析報告
- 顯示適配分數
- 顯示四維度權重解釋
  - 技能匹配度
  - 學歷符合度
  - 工作經驗
  - 專案作品
- 顯示技能缺口
- 顯示優先補強技能
- 顯示薪資影響
- 查看職缺列表
- 收藏 / 取消收藏心儀職缺
- 針對單一職缺執行 AI 分析
- 投遞職缺
- 查看投遞紀錄與 HR 回覆

### HR 端

- HR 登入 / 註冊
- HR 新增職缺
- 查看自己建立的職缺
- 查看各職缺的投遞候選人
- 查看候選人的 AI 分析結果
- 若候選人尚未針對該職缺完成 AI 分析，顯示尚未分析
- 選擇或拒絕候選人
- 填寫 HR 回覆意見

### 後端功能

- 帳號登入與登出
- 帳號註冊
- Session Token 驗證
- 角色權限控管
- 履歷新增 / 更新 / 查詢
- 職缺新增 / 查詢
- 收藏職缺
- 投遞職缺
- HR 更新投遞決策
- AI 分析履歷與最佳匹配職缺
- AI 分析履歷與指定職缺
- 分析結果快取與重複使用
- 分析結果儲存至 Supabase

---

## Demo 操作流程

### 1. 建立 Supabase 專案

請先建立一個 Supabase 專案，並取得：

```txt
SUPABASE_URL
SUPABASE_KEY
```

通常可在 Supabase 專案後台的 Project Settings → API 中找到。

---

### 2. 建立資料表

開啟 Supabase 專案後台：

```txt
SQL Editor
→ New query
→ 貼上 backend/schema.sql
→ Run
```

請確認資料表至少包含以下資料表與欄位：

```txt
users
sessions
resumes
job_postings
analysis_results
applications
```

若資料表是舊版，請確認有補上目前後端會使用到的欄位，例如：

```sql
ALTER TABLE resumes
ADD COLUMN IF NOT EXISTS gender text,
ADD COLUMN IF NOT EXISTS experience jsonb,
ADD COLUMN IF NOT EXISTS projects jsonb,
ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL;

ALTER TABLE job_postings
ADD COLUMN IF NOT EXISTS company text,
ADD COLUMN IF NOT EXISTS created_by uuid;

ALTER TABLE applications
ADD COLUMN IF NOT EXISTS user_id uuid,
ADD COLUMN IF NOT EXISTS hr_decision text,
ADD COLUMN IF NOT EXISTS hr_reply text DEFAULT '';

ALTER TABLE analysis_results
ADD COLUMN IF NOT EXISTS application_id uuid;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS favorite_job_ids text[] DEFAULT '{}';
```

若 HR 選擇候選人時出現 `status` 檢查錯誤，請補上：

```sql
ALTER TABLE applications
DROP CONSTRAINT IF EXISTS applications_status_check;

ALTER TABLE applications
ADD CONSTRAINT applications_status_check
CHECK (status IN ('pending', 'reviewed', 'selected', 'rejected'));
```

---

### 3. 設定後端環境變數

在 `backend/` 資料夾中建立 `.env` 檔案：

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-key
GEMINI_API_KEY=your-gemini-api-key
```

如果沒有設定 `GEMINI_API_KEY`，AI 分析可能會失敗，後端會依目前程式邏輯使用 fallback 分析結果。

---

### 4. 啟動後端

在第一個 terminal：

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install supabase google-genai

uvicorn app.main:app --reload
```

如果使用 Conda：

```bash
cd backend

conda env create -f environment.yml
conda activate webapp

pip install -r requirements.txt
pip install google-genai

uvicorn app.main:app --reload
```

啟動成功後可開啟：

```txt
http://127.0.0.1:8000/docs
```

也可以測試：

```txt
GET /health
```

若回傳：

```json
{
  "status": "ok"
}
```

代表後端已正常啟動。

---

### 5. 啟動前端

在第二個 terminal：

```bash
cd frontend

npm install
npm run dev
```

若前端畫面沒有樣式，可重新確認 Tailwind 相關套件：

```bash
npm install tailwindcss @tailwindcss/vite
```

前端啟動後開啟：

```txt
http://localhost:5173/
```

---

## 前端操作流程

### 求職者流程

```txt
進入平台
→ 求職者入口
→ 註冊或登入求職者帳號
→ 檢視履歷 / 修改履歷
→ 填寫履歷欄位
→ 儲存變更
→ 開始分析
→ 查看履歷分析報告
→ 查看職缺推薦
→ 可針對單一職缺執行 AI 分析
→ 收藏職缺或確認投遞
→ 查看投遞紀錄 / HR 回覆
```

目前履歷欄位包含：

```txt
姓名
性別
學歷
工作經驗
證照
目標職位
期望薪資
技能
專案作品
獎項 / 其他加分項
```

其中姓名由帳號資料帶入，不開放在履歷頁修改。

---

### HR 流程

```txt
進入平台
→ 企業 / HR 入口
→ 註冊或登入 HR 帳號
→ 新增職缺
→ 查看自己建立的職缺
→ 點選職缺查看投遞候選
→ 查看候選人分析摘要
→ 選擇或拒絕候選人
→ 填寫 HR 回覆意見
```

HR 新增職缺時可填寫：

```txt
公司名稱
職缺名稱
需求技能
薪資範圍
最低年資
職缺描述
```

---

## API 端點

### Basic

```txt
GET /              # API 狀態訊息
GET /health        # 健康檢查
```

### Auth

```txt
POST /auth/register
POST /auth/login
POST /auth/logout
```

### Resume

```txt
POST /resume       # 求職者新增或更新履歷
GET /resume/me     # 求職者查看自己的履歷
```

### Analysis

```txt
GET /analyze                 # 分析目前求職者履歷與預設匹配職缺
POST /analyze/job/{job_id}   # 分析目前求職者履歷與指定職缺
GET /analysis-results        # 查看分析紀錄
```

### Jobs

```txt
GET /jobs                         # 查看所有開放職缺
POST /jobs                        # HR 新增職缺
GET /jobs/my                      # HR 查看自己建立的職缺
GET /jobs/{job_id}/applications   # HR 查看某職缺的投遞候選
```

### Applications

```txt
POST /applications
GET /applications/my
PUT /applications/{application_id}/decision
```

### Favorites

```txt
POST /favorites
GET /favorites
```

---

## AI 分析說明

本系統透過結構化 Prompt 將求職者履歷與職缺需求提供給 Gemini API，要求模型回傳固定 JSON 格式的分析結果。

分析結果包含：

```txt
match_score
shap_values
scenario_simulation
salary_impact
priority_skills
skill_gaps
```

其中 `shap_values` 為類 SHAP 權重解釋，包含四個維度：

```txt
skill_match
education
experience
projects
```

前端會將這四個維度視覺化為權重長條圖，協助使用者理解分數背後的主要影響因素。

---

## 注意事項

### 1. 角色入口限制

系統分為：

```txt
求職者入口
企業 / HR 入口
```

若 HR 帳號從求職者入口登入，或求職者帳號從 HR 入口登入，前端會阻止進入錯誤角色頁面。

---

### 2. 註冊功能

目前系統支援註冊帳號。

註冊時會建立：

```txt
username
display_name
password_hash
role
```

密碼會透過 SHA-256 轉換後存入資料庫。

---

### 3. 分析快取

後端會檢查分析結果是否已存在。若履歷資料尚未更新，系統可直接回傳既有分析結果，避免重複呼叫 AI API。

若使用者修改並儲存履歷，後端會更新 `updated_at`，下次分析時即可判斷是否需要重新分析。

---

### 4. 分析結果不是最終決策

本平台定位為決策支援工具，AI 分析結果僅作為參考。

系統不會：

```txt
自動替求職者決定投遞哪個職缺
自動篩選或拒絕求職者
自動修改使用者履歷
自動聯繫 HR
自動安排面試
```

最終投遞與錄取相關決策仍由使用者與 HR 自行判斷。

---

## 開發狀態

目前專案為課程 / Demo 階段版本。

核心重點為：

- 可解釋履歷分析
- 職缺匹配決策支援
- 技能缺口提示
- 前後端 API 串接
- Supabase 資料儲存
- 求職者與 HR 雙端流程
- Gemini API 分析整合

---

## 未來可擴充方向

- 更完整的真實職缺資料庫
- 技能名稱標準化
- 情境模擬功能
- HR 批量候選比較
- 候選人排序與篩選條件
- 使用者實驗與可解釋性評估
- 更完整的權限與資安設計
