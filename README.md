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

## Demo 操作流程

### 1. Supabase 環境變數設定

在 `backend/` 資料夾中建立 `.env` 檔案：

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-legacy-anon-public-key
```

### 2. 啟動後端

在第一個 terminal：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install supabase
uvicorn app.main:app --reload
```

如果使用 Conda：

```bash
cd backend
conda env create -f environment.yml
conda activate webapp
uvicorn app.main:app --reload
```

啟動後開啟：

```txt
http://127.0.0.1:8000/docs
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

## 開發狀態

目前專案為課程 / Demo 階段版本。

核心重點為：

- 可解釋履歷分析
- 職缺匹配決策支援
- 技能缺口提示
- 前後端 API 串接
- Supabase 資料儲存

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

## 常見問題

### 1. 前端畫面沒有樣式

請確認前端已安裝 Tailwind：

```bash
npm install tailwindcss @tailwindcss/vite
```

---

### 2. 前端無法呼叫後端

請確認：

1. 後端正在執行：

```txt
http://127.0.0.1:8000
```

2. 前端正在執行：

```txt
http://localhost:5173
```
