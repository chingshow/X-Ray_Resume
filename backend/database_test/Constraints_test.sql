---- NOT NULL 測試

-- 測試 job_postings.title 的 NOT NULL
INSERT INTO job_postings (title) VALUES (null);
/*
預期：ERROR，違反 NOT NULL 限制
*/

-- 測試 analysis_results 的外鍵
INSERT INTO analysis_results (resume_id, job_id, match_score)
VALUES (
  '00000000-0000-0000-0000-000000000000',
  '00000000-0000-0000-0000-000000000000',
  62
);
/*
預期：ERROR，外鍵指向不存在的記錄
*/


---- CASCADE 刪除測試
-- 先記下一筆 resume 的 id
SELECT id FROM resumes LIMIT 1;

-- 刪除那筆履歷
DELETE FROM resumes WHERE id = '你剛才查到的id';

-- 確認相關的 analysis_results 也被刪掉了
SELECT * FROM analysis_results WHERE resume_id = '你剛才查到的id';

/*
預期：空的，因為 schema.sql 裡有 ON DELETE CASCADE
*/