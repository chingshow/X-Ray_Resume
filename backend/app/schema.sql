-- 1. 使用者擴充資料表（首頁+登入頁面區分求職者與 HR）
CREATE TABLE profiles (
  id uuid REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  role text CHECK (role IN ('jobseeker', 'hr')) NOT NULL,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. 履歷資料表（精準對接「履歷編輯」頁面的所有項目）
CREATE TABLE resumes (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  full_name text,                             -- 姓名
  education text,                             -- 學歷
  experience jsonb,                           -- 工作經歷 (公司、職稱、時間)
  skills text[],                              -- 相關技能關鍵詞 (程式語言、工具/框架、雲端、語言能力)
  projects jsonb,                             -- 專案作品連結
  certifications text[],                      -- 證照
  awards text[],                              -- 獎項
  completion_rate int DEFAULT 0,              -- 整體完成度 (0-100%)
  preferences jsonb,                          -- 求職條件 (期望薪資、目標職位等)
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. 職缺資料表（精準對接「職缺新增/編輯」頁面）
CREATE TABLE job_postings (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  hr_user_id uuid REFERENCES profiles(id) NOT NULL,
  title text NOT NULL,                        -- 設定職缺名
  required_skills text[],                     -- 設定職缺要求中的技能陣列
  description text,                           -- 設定職缺要求中的工作敘述
  min_experience int DEFAULT 0,               -- 工作經驗要求年資
  salary_range text,                          -- 期望年薪/薪資範圍描述
  is_active boolean DEFAULT true,             -- 是否開放中
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. AI 分析結果表（精準對接「履歷分析查看」頁面）
CREATE TABLE analysis_results (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  resume_id uuid REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
  job_id uuid REFERENCES job_postings(id) ON DELETE CASCADE NOT NULL,
  match_score numeric NOT NULL,               -- 分數 (例如: 80)
  skill_gaps text[],                          -- 技能缺口
  explanation text,                           -- 原因 (SHAP 分析)
  shap_values jsonb,                          -- SHAP 視覺化專用 JSON
  salary_impact text,                         -- 薪資變化分析
  priority_skills jsonb,                      -- 系統建議優先補強順序
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. 投遞與互動紀錄表（精準對接「職缺分析、投遞履歷的頁面」與「看有沒有HR要找」）
CREATE TABLE applications (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  resume_id uuid REFERENCES resumes(id) ON DELETE CASCADE NOT NULL,
  job_id uuid REFERENCES job_postings(id) ON DELETE CASCADE NOT NULL,
  analysis_id uuid REFERENCES analysis_results(id),
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'rejected')), -- 狀態
  initiator text DEFAULT 'jobseeker' CHECK (initiator IN ('jobseeker', 'hr')), -- 誰發起的（主動投遞 vs HR找人）
  applied_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);