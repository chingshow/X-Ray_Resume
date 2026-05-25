import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  BarChart3,
  Briefcase,
  CheckCircle2,
  ChevronRight,
  Compass,
  FileText,
  Lightbulb,
  LineChart,
  Pencil,
  Rocket,
  Save,
  Search,
  ShieldCheck,
  Target,
  TrendingUp,
  User,
} from "lucide-react";

const API_BASE = "/api";

const initialResume = {
  full_name: "王小明",
  education: "國立台灣大學 資訊工程學系 學士",
  skills: "Python, FastAPI, PostgreSQL, Docker",
  certifications: "AWS Certified Cloud Practitioner",
  awards: "2023 校內黑客松第二名",
  expected_salary: "NT$800,000/年",
  target_role: "後端工程師 / 全端工程師",
};

const featureList = [
  { icon: Target, title: "職缺適配分析", description: "比較履歷與職缺需求，協助判斷目前適配程度。" },
  { icon: Search, title: "技能缺口定位", description: "整理尚未符合的條件，讓履歷優化方向更明確。" },
  { icon: LineChart, title: "可解釋推薦原因", description: "以文字與權重呈現推薦依據，避免只看到單一分數。" },
  { icon: TrendingUp, title: "薪資影響預估", description: "模擬補強技能後，可能帶來的薪資與職缺變化。" },
  { icon: Compass, title: "行動路徑建議", description: "提供證照、專案與學習方向，幫助規劃下一步。" },
  { icon: Briefcase, title: "HR 初步篩選輔助", description: "協助企業理解候選人與職缺需求之間的符合程度。" },
];

const mockAnalysis = {
  match_score: 72,
  job_snapshot: {
    title: "資深後端工程師",
    required_skills: ["Python", "FastAPI", "Kubernetes", "Redis", "System Design"],
  },
  scenario_simulation: [
    "根據目前履歷，您已具備 Python、FastAPI 與 PostgreSQL 等後端開發基礎，與目標職缺有良好的技術相關性。",
    "若接下來補強 Kubernetes、Redis 與 System Design，整體匹配度有機會明顯提升。建議將雲端部署、快取設計與高併發架構經驗補進履歷，並用具體專案成果呈現。",
  ].join(String.fromCharCode(10, 10)),
  salary_impact: [
    "目前技能組合適合初中階後端工程師職缺。",
    "若補強雲端部署與系統設計能力，可提高進入高階後端或全端職位的機會，薪資談判籌碼也會更完整。",
  ].join(String.fromCharCode(10)),
  priority_skills: [
    { rank: 1, skill: "Kubernetes", reason: "與雲端部署和服務維運高度相關，可提升後端職缺競爭力。" },
    { rank: 2, skill: "Redis", reason: "常用於快取與高併發服務，是後端工程師重要加分技能。" },
    { rank: 3, skill: "System Design", reason: "能展現架構思考能力，對資深職缺影響較大。" },
  ],
};

function splitList(value) {
  return String(value || "")
    .split(/[,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function Card({ children, className = "" }) {
  return (
    <div className={`rounded-[28px] border border-white/70 bg-white/85 shadow-xl shadow-indigo-100/40 backdrop-blur ${className}`}>
      {children}
    </div>
  );
}

function Button({ children, variant = "primary", className = "", ...props }) {
  const styles = {
    primary: "bg-slate-900 text-white shadow-lg shadow-slate-200 hover:bg-slate-800",
    secondary: "bg-white/90 text-slate-800 border border-slate-200 hover:bg-slate-50 hover:border-slate-300",
    ghost: "text-slate-600 hover:bg-white/70",
    soft: "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-100",
  };

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

function Field({ label, value, onChange, multiline = false, disabled = false }) {
  const baseClass = "w-full rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 text-sm outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100 disabled:bg-slate-50 disabled:text-slate-500";

  return (
    <label className="block">
      <span className="mb-2 block text-sm font-semibold text-slate-700">{label}</span>
      {multiline ? (
        <textarea value={value} onChange={(e) => onChange(e.target.value)} rows={4} disabled={disabled} className={baseClass} />
      ) : (
        <input value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} className={baseClass} />
      )}
    </label>
  );
}

function StatusNote({ children, type = "info" }) {
  const styles = {
    info: "border-indigo-100 bg-indigo-50 text-indigo-700",
    success: "border-emerald-100 bg-emerald-50 text-emerald-700",
  };
  return <div className={`rounded-2xl border px-4 py-3 text-sm ${styles[type] || styles.info}`}>{children}</div>;
}

function ScoreRing({ score = 0 }) {
  const normalized = Math.max(0, Math.min(100, Number(score) || 0));
  const background = `conic-gradient(rgb(79 70 229) ${normalized * 3.6}deg, rgb(226 232 240) 0deg)`;

  return (
    <div className="relative grid h-40 w-40 place-items-center rounded-full shadow-inner" style={{ background }}>
      <div className="grid h-28 w-28 place-items-center rounded-full bg-white">
        <div className="text-center">
          <div className="text-4xl font-black text-slate-900">{normalized}</div>
          <div className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Match Score</div>
        </div>
      </div>
    </div>
  );
}

function AppShell({ children }) {
  return (
    <div className="min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,#dbeafe,transparent_35%),radial-gradient(circle_at_top_right,#e0e7ff,transparent_30%),linear-gradient(135deg,#f8fafc,#eef2ff_45%,#f8fafc)] text-slate-900">
      <div className="pointer-events-none fixed left-[-8rem] top-32 h-80 w-80 rounded-full bg-cyan-100/60 blur-3xl" />
      <div className="pointer-events-none fixed bottom-[-8rem] right-[-8rem] h-96 w-96 rounded-full bg-indigo-100/60 blur-3xl" />
      <div className="relative px-5 py-8 md:px-8">{children}</div>
    </div>
  );
}

export default function XRayResumeJobseekerFrontend() {
  const [page, setPage] = useState("landing");
  const [mode, setMode] = useState("view");
  const [resume, setResume] = useState(initialResume);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info");

  const completion = useMemo(() => {
    const fields = Object.values(resume).filter((value) => String(value).trim().length > 0).length;
    return Math.round((fields / Object.keys(resume).length) * 100);
  }, [resume]);

  const setResumeField = (key, value) => setResume((prev) => ({ ...prev, [key]: value }));

  function buildResumePayload() {
    return {
      full_name: resume.full_name,
      education: resume.education,
      skills: splitList(resume.skills),
      certifications: splitList(resume.certifications),
      awards: splitList(resume.awards),
      completion_rate: completion,
      experience: [
        { company: "新創科技股份有限公司", title: "後端工程師", duration: "2022/07 - 2024/06" },
        { company: "學校專題實驗室", title: "研究助理", duration: "2021/09 - 2022/06" },
      ],
      projects: [
        { name: "X-Ray Resume", url: "https://github.com/example/xray-resume" },
      ],
      preferences: {
        expected_salary: resume.expected_salary,
        target_role: resume.target_role,
      },
    };
  }

  async function saveResume() {
    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(`${API_BASE}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildResumePayload()),
      });

      const text = await response.text();
      let data = null;

      if (text) {
        try {
          data = JSON.parse(text);
        } catch {
          data = null;
        }
      }

      if (!response.ok) {
        throw new Error(data?.detail || "save_failed");
      }

      setMessage("履歷已儲存到資料庫，現在可以進行最新履歷分析。");
      setMessageType("success");
      setMode("view");
    } catch (error) {
      setMessage("履歷暫時無法儲存，請確認後端與 Supabase 連線正常後再試一次。");
      setMessageType("info");
    } finally {
      setLoading(false);
    }
  }

  async function runAnalysis() {
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${API_BASE}/analyze`);
      const text = await response.text();
      let data = null;

      if (text) {
        try {
          data = JSON.parse(text);
        } catch {
          data = null;
        }
      }

      if (!response.ok || !data) {
        throw new Error("analysis_unavailable");
      }

      setAnalysis(data);
      setPage("analysis");
    } catch {
      setAnalysis(mockAnalysis);
      setPage("analysis");
      setMessage("目前顯示為預覽分析結果。稍後連線完成後，即可呈現即時資料。");
      setMessageType("info");
    } finally {
      setLoading(false);
    }
  }

  if (page === "landing") {
    return (
      <AppShell>
        <div className="mx-auto max-w-7xl">
          <nav className="mb-10 flex flex-col gap-4 rounded-[28px] border border-white/70 bg-white/75 px-6 py-5 shadow-lg shadow-indigo-100/40 backdrop-blur md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-4">
              <div className="grid h-14 w-14 place-items-center rounded-2xl bg-slate-900 text-white shadow-lg shadow-indigo-100">
                <FileText size={26} />
              </div>
              <div>
                <div className="text-3xl font-black tracking-tight text-slate-950 md:text-4xl">X-Ray Resume</div>
                <div className="text-sm font-semibold text-slate-500 md:text-base">可解釋的履歷分析與職缺匹配平台</div>
              </div>
            </div>
            <Button variant="soft" onClick={() => setPage("home")}>進入平台</Button>
          </nav>

          <div className="grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr]">
            <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55 }}>
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm">
                <Briefcase size={16} /> 給求職者與企業 HR 的雙向決策支援
              </div>

              <div className="mb-4 text-5xl font-black leading-none tracking-tight text-slate-950 md:text-7xl">
                X-Ray Resume
              </div>

              <h1 className="max-w-3xl text-3xl font-black leading-tight tracking-tight text-slate-900 md:text-4xl">
                看見每個人的可能，
                <span className="block text-indigo-700">成就更適合的相遇。</span>
              </h1>

              <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
                這是一個可解釋的履歷分析與職缺匹配平台，協助求職者看懂自身優勢、技能缺口與行動方向，也協助企業 HR 更有效率地理解候選人與職缺需求之間的適配程度。
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <Button onClick={() => setPage("home")} className="px-6 py-3 text-base">
                  求職者入口 <ChevronRight size={18} />
                </Button>
                <Button variant="secondary" className="px-6 py-3 text-base" onClick={() => alert("HR 端可在下一階段加入")}>
                  企業 / HR 入口
                </Button>
              </div>

              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                {["求職者履歷健檢", "企業 HR 初篩輔助", "推薦依據透明"].map((item) => (
                  <div key={item} className="flex items-center gap-2 rounded-2xl bg-white/70 px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm">
                    <CheckCircle2 className="text-emerald-500" size={17} /> {item}
                  </div>
                ))}
              </div>
            </motion.section>

            <motion.section initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.55, delay: 0.1 }}>
              <Card className="p-6 md:p-8">
                <div className="mb-6 flex items-center justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-black text-slate-900">平台功能</h2>
                    <p className="mt-1 text-sm text-slate-500">同時支援求職者的履歷優化，以及企業 HR 的候選人理解與初步篩選。</p>
                  </div>
                  <div className="rounded-2xl bg-slate-900 p-3 text-white shadow-lg shadow-indigo-100">
                    <Rocket size={24} />
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {featureList.map((feature) => {
                    const Icon = feature.icon;
                    return (
                      <div key={feature.title} className="rounded-3xl border border-slate-100 bg-white/75 p-4 transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-indigo-100">
                        <div className="mb-3 grid h-10 w-10 place-items-center rounded-2xl bg-indigo-50 text-indigo-600">
                          <Icon size={20} />
                        </div>
                        <h3 className="font-bold text-slate-900">{feature.title}</h3>
                        <p className="mt-1 text-sm leading-6 text-slate-500">{feature.description}</p>
                      </div>
                    );
                  })}
                </div>
              </Card>
            </motion.section>
          </div>
        </div>
      </AppShell>
    );
  }

  if (page === "home") {
    return (
      <AppShell>
        <div className="mx-auto max-w-7xl">
          <header className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">
            <div>
              <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-white/70 px-4 py-2 text-sm font-semibold text-indigo-700 shadow-sm">
                <User size={16} /> 求職者工作台
              </div>
              <h1 className="text-4xl font-black tracking-tight text-slate-950">歡迎回來，{resume.full_name}</h1>
              <p className="mt-2 text-slate-600">整理履歷、分析職缺適配度，並取得可以實際行動的求職建議。</p>
            </div>
            <Button variant="secondary" onClick={() => setPage("landing")}>返回首頁</Button>
          </header>

          <div className="grid gap-5 lg:grid-cols-[1.35fr_0.65fr]">
            <Card className="p-6 md:p-8">
              <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="flex items-center gap-2 text-2xl font-black"><FileText className="text-indigo-600" /> 我的履歷概況</h2>
                  <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500">確認基本資料與技能內容後，即可產生履歷與職缺的可解釋分析。</p>
                </div>
                <div className="rounded-3xl bg-gradient-to-br from-indigo-50 to-sky-50 px-5 py-4 text-center">
                  <div className="text-3xl font-black text-indigo-700">{completion}%</div>
                  <div className="text-xs font-semibold text-slate-500">履歷完整度</div>
                </div>
              </div>

              <div className="mt-7 grid gap-4 md:grid-cols-3">
                <div className="rounded-3xl bg-white/75 p-5 shadow-sm">
                  <div className="text-xs font-bold uppercase tracking-wide text-slate-400">Education</div>
                  <p className="mt-2 text-sm font-semibold leading-6 text-slate-800">{resume.education}</p>
                </div>
                <div className="rounded-3xl bg-white/75 p-5 shadow-sm">
                  <div className="text-xs font-bold uppercase tracking-wide text-slate-400">Target</div>
                  <p className="mt-2 text-sm font-semibold leading-6 text-slate-800">{resume.target_role}</p>
                </div>
                <div className="rounded-3xl bg-white/75 p-5 shadow-sm">
                  <div className="text-xs font-bold uppercase tracking-wide text-slate-400">Salary</div>
                  <p className="mt-2 text-sm font-semibold leading-6 text-slate-800">{resume.expected_salary}</p>
                </div>
              </div>

              <div className="mt-5 rounded-3xl bg-slate-900 p-5 text-white shadow-lg shadow-slate-200">
                <div className="text-sm font-semibold text-white/75">核心技能</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {splitList(resume.skills).map((skill) => (
                    <span key={skill} className="rounded-full bg-white/15 px-3 py-1 text-sm font-semibold backdrop-blur">{skill}</span>
                  ))}
                </div>
              </div>

              <div className="mt-7 flex flex-wrap gap-3">
                <Button variant="secondary" onClick={() => { setMode("view"); setPage("resume"); }}>檢視履歷</Button>
                <Button variant="secondary" onClick={() => { setMode("edit"); setPage("resume"); }}><Pencil size={16} /> 修改履歷</Button>
                <Button onClick={runAnalysis} disabled={loading}><BarChart3 size={16} /> {loading ? "分析中..." : "開始分析"}</Button>
              </div>
            </Card>

            <div className="space-y-5">
              <Card className="p-6">
                <h2 className="flex items-center gap-2 text-xl font-black"><Lightbulb className="text-amber-500" /> 建議流程</h2>
                <div className="mt-5 space-y-3">
                  {["確認履歷完整度", "選擇目標職缺", "查看技能缺口", "規劃補強路徑"].map((step, index) => (
                    <div key={step} className="flex items-center gap-3 rounded-2xl bg-white/75 p-3 text-sm font-semibold text-slate-700">
                      <div className="grid h-8 w-8 place-items-center rounded-xl bg-indigo-50 text-indigo-600">{index + 1}</div>
                      {step}
                    </div>
                  ))}
                </div>
              </Card>

              <Card className="p-6">
                <h2 className="flex items-center gap-2 text-xl font-black"><Briefcase className="text-violet-600" /> 其他功能</h2>
                <div className="mt-5 space-y-3">
                  <Button variant="secondary" className="w-full justify-start" onClick={() => alert("職缺推薦功能將於下一階段加入")}>職缺推薦</Button>
                  <Button variant="secondary" className="w-full justify-start" onClick={() => alert("投遞紀錄功能將於下一階段加入")}>投遞紀錄</Button>
                  <Button variant="secondary" className="w-full justify-start" onClick={() => alert("AI 職涯顧問功能將於下一階段加入")}>AI 職涯顧問</Button>
                </div>
              </Card>
            </div>
          </div>

          {message && <div className="mt-5"><StatusNote type={messageType}>{message}</StatusNote></div>}
        </div>
      </AppShell>
    );
  }

  if (page === "resume") {
    const readOnly = mode === "view";
    return (
      <AppShell>
        <div className="mx-auto max-w-5xl">
          <Button variant="ghost" onClick={() => setPage("home")} className="mb-5"><ArrowLeft size={16} /> 返回工作台</Button>
          <Card className="p-6 md:p-8">
            <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div>
                <h1 className="text-3xl font-black">{readOnly ? "檢視履歷" : "修改履歷"}</h1>
                <p className="mt-2 text-sm text-slate-500">補齊學歷、技能、證照與職涯目標，能讓後續分析更完整。</p>
              </div>
              <Button variant="secondary" onClick={() => setMode(readOnly ? "edit" : "view")}>{readOnly ? "切換成修改" : "切換成檢視"}</Button>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <Field label="姓名" value={resume.full_name} onChange={(v) => setResumeField("full_name", v)} disabled={readOnly} />
              <Field label="目標職位" value={resume.target_role} onChange={(v) => setResumeField("target_role", v)} disabled={readOnly} />
              <Field label="學歷" value={resume.education} onChange={(v) => setResumeField("education", v)} multiline disabled={readOnly} />
              <Field label="技能 (逗號分隔)" value={resume.skills} onChange={(v) => setResumeField("skills", v)} multiline disabled={readOnly} />
              <Field label="證照" value={resume.certifications} onChange={(v) => setResumeField("certifications", v)} multiline disabled={readOnly} />
              <Field label="獎項 / 其他加分項" value={resume.awards} onChange={(v) => setResumeField("awards", v)} multiline disabled={readOnly} />
              <Field label="期望薪資" value={resume.expected_salary} onChange={(v) => setResumeField("expected_salary", v)} disabled={readOnly} />
            </div>

            <div className="mt-7 flex flex-wrap gap-3">
              <Button onClick={saveResume} disabled={loading || readOnly}><Save size={16} /> {loading ? "儲存中..." : "儲存變更"}</Button>
              <Button variant="secondary" onClick={runAnalysis} disabled={loading}><BarChart3 size={16} /> 查看分析</Button>
            </div>
            {message && <div className="mt-5"><StatusNote type={messageType}>{message}</StatusNote></div>}
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl">
        <Button variant="ghost" onClick={() => setPage("home")} className="mb-5"><ArrowLeft size={16} /> 返回工作台</Button>
        {message && <div className="mb-5"><StatusNote type={messageType}>{message}</StatusNote></div>}

        <div className="grid gap-5 lg:grid-cols-[0.78fr_1.22fr]">
          <Card className="grid place-items-center p-7 text-center">
            <ScoreRing score={analysis?.match_score ?? 0} />
            <h1 className="mt-6 text-3xl font-black">履歷分析報告</h1>
            <p className="mt-2 text-sm text-slate-500">目標職缺：{analysis?.job_snapshot?.title || "推薦職缺"}</p>
            <div className="mt-5 flex flex-wrap justify-center gap-2">
              {(analysis?.job_snapshot?.required_skills || []).map((skill) => (
                <span key={skill} className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">{skill}</span>
              ))}
            </div>
          </Card>

          <Card className="p-6 md:p-8">
            <h2 className="flex items-center gap-2 text-2xl font-black"><ShieldCheck className="text-emerald-500" /> 為什麼這樣推薦？</h2>
            <p className="mt-4 whitespace-pre-line rounded-3xl bg-white/75 p-5 text-sm leading-7 text-slate-700 shadow-sm">
              {analysis?.scenario_simulation || "目前正在整理分析結果。"}
            </p>
          </Card>
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-3">
          <Card className="p-6 lg:col-span-2">
            <h2 className="flex items-center gap-2 text-2xl font-black"><Rocket className="text-violet-600" /> 優先補強技能</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-3">
              {(analysis?.priority_skills || []).map((item) => (
                <div key={item.rank} className="rounded-3xl border border-slate-100 bg-white/75 p-5 shadow-sm">
                  <div className="mb-4 grid h-10 w-10 place-items-center rounded-2xl bg-slate-900 font-black text-white">{item.rank}</div>
                  <h3 className="font-black text-slate-900">{item.skill}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">{item.reason}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="flex items-center gap-2 text-2xl font-black"><TrendingUp className="text-sky-600" /> 薪資影響</h2>
            <p className="mt-4 whitespace-pre-line rounded-3xl bg-white/75 p-5 text-sm leading-7 text-slate-700 shadow-sm">
              {analysis?.salary_impact || "目前正在整理薪資影響。"}
            </p>
          </Card>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <Button variant="secondary" onClick={() => alert("投遞履歷功能將於下一階段加入")}>投遞履歷</Button>
          <Button variant="secondary" onClick={() => alert("情境模擬功能將於下一階段加入")}>情境模擬</Button>
          <Button onClick={() => setPage("resume")}>回去優化履歷</Button>
        </div>
      </div>
    </AppShell>
  );
}
