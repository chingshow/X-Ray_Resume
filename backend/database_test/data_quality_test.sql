-- 確認 skills 真的是陣列格式，不是字串
SELECT 
  full_name,
  skills,
  pg_typeof(skills) AS 型別
FROM resumes;
-- 型別應該顯示 text[]，不是 text

-- 確認 experience 是合法的 JSON
SELECT 
  full_name,
  experience,
  jsonb_typeof(experience) AS json型別
FROM resumes
WHERE experience IS NOT NULL;
-- json型別應該顯示 array