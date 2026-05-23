# Readme

## 使用方式
### 後端
在terminal依序輸入
1. cd Backend
2. 如果第一次用: conda env create -f environment.yml -- 他會建一個叫做webapp的環境用來執行程式
3. conda activate webapp
4. uvicorn app.main:app --reload
5. 到瀏覽器 http://127.0.0.1:8000/docs