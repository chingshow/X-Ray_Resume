-- 確認 analysis_results 可以正確 JOIN 回履歷和職缺
SELECT 
    ar.id AS 分析id,
    ar.match_score AS 匹配分數,
    r.full_name AS 求職者姓名,
    jp.title AS 職缺名稱,
    ar.created_at AS 分析時間
FROM analysis_results ar
JOIN resumes r ON ar.resume_id = r.id
JOIN job_postings jp ON ar.job_id = jp.id
ORDER BY ar.created_at DESC;
/*
預期：每一行都有完整資料，不會有 null 欄位
*/



-- 確認沒有孤兒資料，回傳孤兒記錄的所有欄位
SELECT ar.*
FROM analysis_results ar
LEFT JOIN resumes r ON ar.resume_id = r.id
WHERE r.id IS NULL;

-- 檢查 analysis_results 有沒有指向不存在職缺的記錄，查 job_id 指向不存在職缺的記錄
SELECT ar.*
FROM analysis_results ar
LEFT JOIN job_postings jp ON ar.job_id = jp.id
WHERE jp.id IS NULL;

/*
空的，代表所有關聯都是有效的
*/


-- 查詢所有外鍵關聯
SELECT
    tc.table_name AS 資料表,
    kcu.column_name AS 欄位,
    ccu.table_name AS 關聯到的資料表,
    ccu.column_name AS 關聯到的欄位,
    rc.delete_rule AS 刪除規則
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name;

/*
預期結果：
顯示 schema.sql 裡面的每一條 REFERENCES
*/

-- 因為 profile REFERENCE 的 auth.users 是內建的，用 tc.table_schema = 'public' 不會顯示

SELECT
    conname AS 外鍵名稱,
    conrelid::regclass AS 資料表,
    confrelid::regclass AS 關聯到
FROM pg_constraint
WHERE contype = 'f'
    AND conrelid::regclass::text = 'profiles';

/*
預期結果：
有資料表 profiles 關聯到 auth.user
*/