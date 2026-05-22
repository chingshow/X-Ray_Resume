-- ============================================================
-- X-Ray Resume Schema
-- ============================================================

-- 1. 使用者擴充資料表
CREATE TABLE IF NOT EXISTS profiles (
  id uuid REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  role text CHECK (role IN ('jobseeker', 'hr')) NOT NULL,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. 履歷資料表
--    開發階段：user_id 設為 NULLABLE，方便直接在 /docs 測試而不需要 auth
--    上線前：移除 NULLABLE，改為 NOT NULL，並在 API 中從 JWT 取得 user_id
CREATE TABLE IF NOT EXISTS resumes (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,   -- 開發中暫時 NULLABLE
  full_name text,
  education text,
  experience jsonb,
  skills text[],
  projects jsonb,
  certifications text[],
  awards text[],
  completion_rate int DEFAULT 0,
  preferences jsonb,
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. 職缺資料表
CREATE TABLE IF NOT EXISTS job_postings (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  hr_user_id uuid REFERENCES profiles(id),                  -- 開發中暫時 NULLABLE
  title text NOT NULL,
  required_skills text[],
  description text,
  min_experience int DEFAULT 0,
  salary_range text,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. AI 分析結果表
CREATE TABLE IF NOT EXISTS analysis_results (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  resume_id uuid REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
  job_id uuid REFERENCES job_postings(id) ON DELETE CASCADE NOT NULL,
  match_score numeric NOT NULL,
  skill_gaps text[],
  explanation text,
  shap_values jsonb,
  salary_impact text,
  priority_skills jsonb,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. 投遞與互動紀錄表
CREATE TABLE IF NOT EXISTS applications (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  resume_id uuid REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
  job_id uuid REFERENCES job_postings(id) ON DELETE CASCADE NOT NULL,
  analysis_id uuid REFERENCES analysis_results(id),
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'rejected')),
  initiator text DEFAULT 'jobseeker' CHECK (initiator IN ('jobseeker', 'hr')),
  applied_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);


-- ============================================================
-- 開發用測試資料（Seed Data）
-- 在 Supabase SQL Editor 執行這段，即可讓 GET /analyze 正常運作
-- ============================================================

-- 插入一筆測試履歷（user_id 留空，因為開發階段不需要 auth）
INSERT INTO resumes (full_name, education, experience, skills, projects, certifications, awards, completion_rate, preferences)
VALUES (
  '王小明',
  '國立台灣大學 資訊工程學系 學士',
  '[
    {"company": "新創科技股份有限公司", "title": "後端工程師", "duration": "2022/07 - 2024/06"},
    {"company": "學校專題實驗室", "title": "研究助理", "duration": "2021/09 - 2022/06"}
  ]'::jsonb,
  ARRAY['Python', 'FastAPI', 'PostgreSQL', 'Docker'],
  '[{"name": "X-Ray Resume", "url": "https://github.com/example/xray-resume"}]'::jsonb,
  ARRAY['AWS Certified Cloud Practitioner'],
  ARRAY['2023 校內黑客松第二名'],
  80,
  '{"expected_salary": "NT$800,000/年", "target_role": "後端工程師 / 全端工程師"}'::jsonb
);

-- 插入一筆測試職缺（hr_user_id 留空）
INSERT INTO job_postings (title, required_skills, description, min_experience, salary_range, is_active)
VALUES (
  '資深後端工程師',
  ARRAY['Python', 'FastAPI', 'Kubernetes', 'Redis', 'System Design'],
  '負責設計與開發高併發後端服務，需具備雲端部署與系統架構設計能力。',
  3,
  'NT$1,000,000 – NT$1,500,000/年',
  true
);