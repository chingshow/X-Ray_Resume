# Readme
# X-Ray Resume
X-Ray Resume 是一個可解釋的履歷分析與職缺匹配決策支援 Web 平台。  
平台協助求職者檢視履歷、了解技能缺口與職缺適配度，也可作為企業 HR 初步理解候選人與職缺需求之間關聯的輔助工具。

## 專案結構
X-Ray_Resume/
├── backend/      # FastAPI 後端
├── frontend/     # React + Vite 前端
├── README.md
└── .gitignore

## 使用方式
### 後端
在terminal依序輸入
1. cd Backend
2. 如果第一次用: conda env create -f environment.yml -- 他會建一個叫做webapp的環境用來執行程式
3. conda activate webapp
4. uvicorn app.main:app --reload
5. 到瀏覽器 http://127.0.0.1:8000/docs
