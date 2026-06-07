-- 確認所有資料表存在
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- 預期看到：
/*
analysis_results
applications
job_postings
profiles
resumes
*/


-- 資料表的欄位定義：一次確認三張核心資料表的欄位定義，對照schema.sql 檢查一遍，人工確認正確就好
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name IN ('resumes', 'job_postings', 'analysis_results')
ORDER BY table_name, ordinal_position;