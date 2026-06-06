import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertCircle,
  ArrowLeft,
  BarChart3,
  Briefcase,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Compass,
  Database,
  FileText,
  Lightbulb,
  LineChart,
  Lock,
  LogOut,
  Pencil,
  RefreshCw,
  Rocket,
  Save,
  Search,
  Send,
  ShieldCheck,
  Target,
  TrendingUp,
  User,
  Users,
} from "lucide-react";

const API_BASE = "";

// ---------------------------------------------------------------------------
// Auth-aware fetch helper
// ---------------------------------------------------------------------------
let _authToken = null;

function setAuthToken(token) {
  _authToken = token;
}

function getAuthToken() {
  return _authToken;
}

const emptyResume = {
  full_name: "",
  education: "",
  skills: "",
  certifications: "",
  awards: "",
  expected_salary: "",
  target_role: "",
};

const initialResume = {
  full_name: "王小明",
  education: "國立台灣大學 資訊工程學系 學士",
  skills: "Python, FastAPI, PostgreSQL, Docker",
  certifications: "AWS Certified Cloud Practitioner",
  awards: "2023 校內黑客松第二名",
  expected_salary: "NT$800,000/年",
  target_role: "後端工程師 / 全端工程師",
};

const initialJobRequirement = {
  title: "資深後端工程師",
  company: "金融科技公司 A",
  required_skills: "Python, FastAPI, Kubernetes, Redis, System Design",
  salary_range: "NT$1,000,000 – NT$1,500,000/年",
  min_experience: "3",
  description: "負責設計與開發高併發後端服務，需具備雲端部署與系統架構設計能力。",
};

const initialLogin = {
  username: "",
  password: "",
};

const initialRegister = {
  display_name: "",
  username: "",
  password: "",
};

const featureList = [
  { icon: Target, title: "職缺適配分析", description: "比較履歷與職缺需求，協助判斷目前適配程度。" },
  { icon: Search, title: "技能缺口定位", description: "整理尚未符合的條件，讓履歷優化方向更明確。" },
  { icon: LineChart, title: "可解釋推薦原因", description: "以文字與權重呈現推薦依據，避免只看到單一分數。" },
  { icon: TrendingUp, title: "薪資影響預估", description: "模擬補強技能後，可能帶來的薪資與職缺變化。" },
  { icon: Compass, title: "行動路徑建議", description: "提供證照、專案與學習方向，幫助規劃下一步。" },
  { icon: Briefcase, title: "HR 初步篩選輔助", description: "協助企業理解候選與職缺需求之間的符合程度。" },
];

const mockAnalysis = {
  match_score: 72,
  resume_snapshot: {
    full_name: "王小明",
    education: "國立台灣大學 資訊工程學系 學士",
    skills: ["Python", "FastAPI", "PostgreSQL", "Docker"],
  },
  job_snapshot: {
    title: "資深後端工程師",
    required_skills: ["Python", "FastAPI", "Kubernetes", "Redis", "System Design"],
  },
  shap_values: {
    skill_match: 0.45,
    education: 0.2,
    experience: 0.25,
    projects: 0.1,
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

const initialJobList = [];
const initialApplications = [];

function splitList(value) {
  return String(value || "")
    .split(/[,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

async function requestJSON(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    ...(options.headers || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
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
    throw new Error(data?.detail || data?.message || `API error: ${response.status}`);
  }

  return data;
}

function getScoreLevel(score) {
  const value = Number(score) || 0;

  if (value >= 75) {
    return { label: "高適配", className: "bg-emerald-50 text-emerald-700 border-emerald-100" };
  }

  if (value >= 60) {
    return { label: "中適配", className: "bg-amber-50 text-amber-700 border-amber-100" };
  }

  return { label: "待補強", className: "bg-rose-50 text-rose-700 border-rose-100" };
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
    primary:
      "bg-slate-900 text-white shadow-lg shadow-slate-200 hover:-translate-y-1 hover:scale-[1.02] hover:bg-indigo-700 hover:shadow-2xl hover:shadow-indigo-200 active:translate-y-0 active:scale-[0.99]",
    secondary:
      "bg-white/90 text-slate-800 border border-slate-200 hover:-translate-y-1 hover:scale-[1.02] hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-300 hover:shadow-xl hover:shadow-indigo-100 active:translate-y-0 active:scale-[0.99]",
    ghost:
      "text-slate-600 hover:bg-white/80 hover:text-indigo-700 hover:shadow-md active:scale-[0.99]",
    soft:
      "bg-indigo-50 text-indigo-700 hover:-translate-y-1 hover:scale-[1.02] hover:bg-indigo-100 border border-indigo-100 hover:shadow-lg hover:shadow-indigo-100 active:scale-[0.99]",
    danger:
      "bg-rose-50 text-rose-700 hover:-translate-y-1 hover:scale-[1.02] hover:bg-rose-100 border border-rose-100 hover:shadow-lg hover:shadow-rose-100 active:scale-[0.99]",
    success:
      "bg-emerald-50 text-emerald-700 hover:-translate-y-1 hover:scale-[1.02] hover:bg-emerald-100 border border-emerald-100 hover:shadow-lg hover:shadow-emerald-100 active:scale-[0.99]",
  };

  return (
    <button
      className={`inline-flex cursor-pointer items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

function Field({
  label,
  value,
  onChange,
  multiline = false,
  disabled = false,
  type = "text",
  placeholder = "",
  required = false,
  helpText = "",
}) {
  const baseClass =
    "w-full rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 text-sm outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100 disabled:bg-slate-50 disabled:text-slate-500";

  return (
    <label className="block">
      <span className="mb-2 block text-sm font-semibold text-slate-700">
        {label}
        {required && <span className="ml-1 text-rose-500">*</span>}
      </span>
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={4}
          disabled={disabled}
          className={baseClass}
          placeholder={placeholder}
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={baseClass}
          placeholder={placeholder}
        />
      )}
      {helpText && <span className="mt-1 block text-xs leading-5 text-slate-400">{helpText}</span>}
    </label>
  );
}

function StatusNote({ children, type = "info" }) {
  const styles = {
    info: "border-indigo-100 bg-indigo-50 text-indigo-700",
    success: "border-emerald-100 bg-emerald-50 text-emerald-700",
    warning: "border-amber-100 bg-amber-50 text-amber-700",
    error: "border-rose-100 bg-rose-50 text-rose-700",
  };

  return <div className={`rounded-2xl border px-4 py-3 text-sm ${styles[type] || styles.info}`}>{children}</div>;
}

function LoadingOverlay({
  show,
  title = "處理中...",
  description = "可能需要幾秒鐘，請稍候，請勿關閉頁面。",
}) {
  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 px-5 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-[32px] bg-white p-8 text-center shadow-2xl shadow-slate-900/20">
        <div className="mx-auto mb-5 h-14 w-14 animate-spin rounded-full border-4 border-indigo-100 border-t-indigo-600" />
        <h2 className="text-2xl font-black text-slate-900">{title}</h2>
        <p className="mt-3 text-sm font-semibold leading-6 text-indigo-600">{description}</p>
      </div>
    </div>
  );
}

function ScoreRing({ score = 0 }) {
  const normalized = Math.max(0, Math.min(100, Number(score) || 0));
  const background = `conic-gradient(rgb(79 70 229) ${normalized * 3.6}deg, rgb(226 232 240) 0deg)`;

  return (
    <div className="relative grid h-40 w-40 shrink-0 place-items-center rounded-full shadow-inner" style={{ background, minWidth: "10rem", minHeight: "10rem" }}>
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

function TopLogout({ onLogout }) {
  return (
    <div className="flex justify-end pt-1">
      <Button variant="secondary" onClick={onLogout}>
        <LogOut size={16} /> 登出
      </Button>
    </div>
  );
}

function MiniMetric({ label, value, icon: Icon }) {
  return (
    <div className="rounded-3xl bg-white/75 p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-xs font-bold uppercase tracking-wide text-slate-400">{label}</div>
          <div className="mt-2 text-2xl font-black text-slate-900">{value}</div>
        </div>
        {Icon && <Icon className="text-indigo-600" size={24} />}
      </div>
    </div>
  );
}

export default function XRayResumeJobseekerFrontend() {
  const [page, setPage] = useState("landing");
  const [selectedRole, setSelectedRole] = useState("jobseeker");
  const [login, setLogin] = useState(initialLogin);
  const [registerForm, setRegisterForm] = useState(initialRegister);
  const [currentUser, setCurrentUser] = useState(null);
  const [authToken, setAuthTokenState] = useState(null);

  const [mode, setMode] = useState("view");
  const [resume, setResume] = useState(initialResume);
  const [jobRequirement, setJobRequirement] = useState(initialJobRequirement);
  const [jobList, setJobList] = useState(initialJobList);
  const [selectedHrJobId, setSelectedHrJobId] = useState(null);

  const [favoriteJobIds, setFavoriteJobIds] = useState([]);
  const [applications, setApplications] = useState(initialApplications);
  const [analysis, setAnalysis] = useState(null);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [hrCandidates, setHrCandidates] = useState([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);
  const [hrReplyDraft, setHrReplyDraft] = useState("");

  const [apiStatus, setApiStatus] = useState("unknown");
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState(null);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info");

  const completion = useMemo(() => {
    const required = [resume.full_name, resume.education, resume.skills, resume.expected_salary, resume.target_role];
    const filledRequired = required.filter((value) => String(value || "").trim().length > 0).length;
    const optional = [resume.certifications, resume.awards].filter((value) => String(value || "").trim().length > 0).length;
    return Math.min(100, Math.round(((filledRequired + optional * 0.5) / 6) * 100));
  }, [resume]);

  const selectedHrJob = jobList.find((job) => job.id === selectedHrJobId) || jobList[0] || null;

  const candidatesForSelectedJob = useMemo(() => {
    return hrCandidates.filter((candidate) => candidate.appliedJobId === selectedHrJob?.id);
  }, [hrCandidates, selectedHrJob]);

  const selectedCandidate =
    hrCandidates.find((candidate) => candidate.id === selectedCandidateId) || candidatesForSelectedJob[0] || null;

  const candidateStats = useMemo(() => {
    const total = jobList.reduce((sum, job) => sum + (job.application_count ?? 0), 0);
    const high = candidatesForSelectedJob.filter((candidate) => candidate.hasAnalysis && Number(candidate.score) >= 75).length;
    const medium = candidatesForSelectedJob.filter(
      (candidate) => candidate.hasAnalysis && Number(candidate.score) >= 60 && Number(candidate.score) < 75
    ).length;

    return { total, high, medium };
  }, [jobList, candidatesForSelectedJob]);

  const setResumeField = (key, value) => setResume((prev) => ({ ...prev, [key]: value }));
  const setJobField = (key, value) => setJobRequirement((prev) => ({ ...prev, [key]: value }));

  function showMessage(text, type = "info") {
    setMessage(text);
    setMessageType(type);
  }

  function validateResumeForSave() {
    const requiredFields = [
      ["姓名", currentUser?.display_name || resume.full_name],
      ["目標職位", resume.target_role],
      ["學歷", resume.education],
      ["技能", resume.skills],
      ["期望薪資", resume.expected_salary],
    ];
    const missing = requiredFields.filter(([, value]) => !String(value || "").trim()).map(([label]) => label);

    if (missing.length > 0) {
      showMessage(`請先補齊必填欄位：${missing.join("、")}。`, "warning");
      return false;
    }

    return true;
  }

  async function logout() {
    try {
      await requestJSON("/auth/logout", { method: "POST" });
    } catch {
      // silently ignore logout errors
    }
    setAuthToken(null);
    setAuthTokenState(null);
    setCurrentUser(null);
    setLogin(initialLogin);
    setRegisterForm(initialRegister);
    setMessage("");
    setJobList([]);
    setApplications([]);
    setFavoriteJobIds([]);
    setHrCandidates([]);
    setResume(initialResume);
    setPage("landing");
  }

  function goLogin(role) {
    setSelectedRole(role);
    setMessage("");
    setLogin(initialLogin);
    setRegisterForm(initialRegister);
    setPage("login");
  }

  function goRegister() {
    setMessage("");
    setRegisterForm(initialRegister);
    setPage("register");
  }

  function handleDemoRegister(event) {
    event.preventDefault();
    showMessage(
      "目前 Demo 版本不開放自行註冊，請使用測試帳號登入。",
      "info"
    );
  }

  async function handleLogin(event) {
    event.preventDefault();

    if (!login.username.trim() || !login.password.trim()) {
      showMessage("請輸入使用者名稱與密碼。", "warning");
      return;
    }

    setLoading(true);
    setLoadingText("登入中...");
    setMessage("");

    try {
      const data = await requestJSON("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username: login.username.trim(), password: login.password.trim() }),
      });

      setAuthToken(data.token);
      setAuthTokenState(data.token);

      const role = data.user.role;
      if (role !== selectedRole) {
        await requestJSON("/auth/logout", { method: "POST" }).catch(() => {});
        setAuthToken(null);
        setAuthTokenState(null);
        setCurrentUser(null);
        showMessage(
          selectedRole === "jobseeker"
            ? "此帳號不是求職者帳號，請改用企業 / HR 入口登入。"
            : "此帳號不是 HR 帳號，請改用求職者入口登入。",
          "error"
        );
        return;
      }

      setCurrentUser(data.user);
      showMessage(`歡迎回來，${data.user.display_name || data.user.username}！`, "success");

      if (role === "hr") {
        setPage("hr");
        await loadHrJobs(true);
      } else {
        setResume((prev) => ({
          ...prev,
          full_name: data.user.display_name || data.user.username || prev.full_name,
        }));
        setPage("home");
        await Promise.all([loadMyResume(true, data.user), loadJobs(true), loadFavorites(true), loadMyApplications(true)]);
      }
    } catch (error) {
      console.error("登入 API 錯誤：", error);
      showMessage(error.message || "帳號或密碼錯誤，請重試。", "error");
    } finally {
      setLoading(false);
      setLoadingText(null);
    }
  }

  function buildResumePayload() {
    return {
      full_name: currentUser?.display_name || resume.full_name,
      education: resume.education,
      skills: splitList(resume.skills),
      certifications: splitList(resume.certifications),
      awards: splitList(resume.awards),
      completion_rate: completion,
      experience: [
        { company: "新創科技股份有限公司", title: "後端工程師", duration: "2022/07 - 2024/06" },
        { company: "學校專題實驗室", title: "研究助理", duration: "2021/09 - 2022/06" },
      ],
      projects: [{ name: "X-Ray Resume", url: "https://github.com/example/xray-resume" }],
      preferences: {
        expected_salary: resume.expected_salary,
        target_role: resume.target_role,
      },
    };
  }

  function buildJobPayload(job = jobRequirement) {
    return {
      title: job.title,
      company: job.company,
      description: job.description,
      required_skills: Array.isArray(job.required_skills) ? job.required_skills : splitList(job.required_skills),
      salary_range: job.salary_range,
      min_experience: Number(job.min_experience) || 0,
    };
  }

  async function loadMyResume(silent = false, userOverride = null) {
    if (!silent) {
      setLoading(true);
      setLoadingText("載入履歷中...");
    }
    try {
      const data = await requestJSON("/resume/me");
      const displayName = userOverride?.display_name || currentUser?.display_name || userOverride?.username || currentUser?.username || "";
      if (data?.data) {
        const r = data.data;
        setResume({
          full_name: r.full_name || displayName,
          education: r.education || "",
          skills: Array.isArray(r.skills) ? r.skills.join(", ") : r.skills || "",
          certifications: Array.isArray(r.certifications) ? r.certifications.join(", ") : r.certifications || "",
          awards: Array.isArray(r.awards) ? r.awards.join(", ") : r.awards || "",
          expected_salary: r.preferences?.expected_salary || "",
          target_role: r.preferences?.target_role || "",
        });
      } else {
        setResume({ ...emptyResume, full_name: displayName });
      }
    } catch (error) {
      console.warn("載入履歷失敗：", error.message);
      if (!silent) showMessage("無法載入履歷：" + error.message, "warning");
    } finally {
      if (!silent) {
        setLoading(false);
        setLoadingText(null);
      }
    }
  }

  async function loadJobs(silent = false) {
    if (!silent) {
      setLoading(true);
      setLoadingText("載入職缺中...");
    }
    try {
      const data = await requestJSON("/jobs");
      const list = Array.isArray(data) ? data : [];
      setJobList(list);
    } catch (error) {
      console.warn("載入職缺失敗：", error.message);
      setJobList([]);
      if (!silent) showMessage("目前無法載入後端職缺，請確認 API 或登入狀態。", "warning");
    } finally {
      if (!silent) {
        setLoading(false);
        setLoadingText(null);
      }
    }
  }

  async function loadFavorites(silent = false) {
    try {
      const data = await requestJSON("/favorites");
      setFavoriteJobIds(data?.favorite_job_ids || []);
    } catch (error) {
      console.warn("載入收藏失敗：", error.message);
      if (!silent) showMessage("無法載入收藏狀態：" + error.message, "warning");
    }
  }

  async function loadMyApplications(silent = false) {
    if (!silent) {
      setLoading(true);
      setLoadingText("載入投遞紀錄中...");
    }
    try {
      const data = await requestJSON("/applications/my");
      const list = Array.isArray(data) ? data : [];
      const mapped = list.map((item) => ({
        id: item.id,
        jobId: item.job_id,
        jobTitle: item.job_postings?.title || "職缺名稱",
        company: item.job_postings?.company || "",
        status: statusLabel(item.status, item.hr_decision),
        reply: item.hr_reply ? `HR 回覆：${item.hr_reply}` : "HR 尚未回覆。",
        createdAt: item.created_at ? new Date(item.created_at).toLocaleDateString("zh-TW") : "",
      }));
      setApplications(mapped);
      return mapped;
    } catch (error) {
      console.warn("載入投遞紀錄失敗：", error.message);
      if (!silent) showMessage("無法載入投遞紀錄：" + error.message, "warning");
      return [];
    } finally {
      if (!silent) {
        setLoading(false);
        setLoadingText(null);
      }
    }
  }

  function statusLabel(status, hrDecision) {
    if (hrDecision === "selected") return "已錄取";
    if (hrDecision === "rejected") return "未錄取";
    if (status === "pending") return "已投遞，等待 HR 回覆";
    return status || "已投遞";
  }

  async function loadHrJobs(silent = false) {
    if (!silent) {
      setLoading(true);
      setLoadingText("載入 HR 職缺中...");
    }
    try {
      const data = await requestJSON("/jobs/my");
      const list = Array.isArray(data) ? data : [];
      setJobList(list.map((job) => ({ ...job, application_count: job.application_count ?? 0 })));
      if (list.length > 0) setSelectedHrJobId((prev) => prev || list[0].id);
    } catch (error) {
      console.warn("載入 HR 職缺失敗：", error.message);
      if (!silent) showMessage("無法載入 HR 職缺：" + error.message, "warning");
    } finally {
      if (!silent) {
        setLoading(false);
        setLoadingText(null);
      }
    }
  }

  async function loadJobApplications(jobId) {
    if (!jobId) return;
    setLoading(true);
    setLoadingText("載入候選資料中...");
    try {
      const data = await requestJSON(`/jobs/${jobId}/applications`);
      const list = Array.isArray(data) ? data : [];
      const candidates = list.map((item, index) => {
        const resumeData = item.resumes || {};
        const analysisData = Array.isArray(item.analysis_results) && item.analysis_results.length > 0 ? item.analysis_results[0] : null;
        const userData = resumeData.users || {};

        return {
          id: item.id,
          appId: item.id,
          name: userData.display_name || resumeData.full_name || `候選 ${index + 1}`,
          target: resumeData.preferences?.target_role || "未填寫目標職位",
          hasAnalysis: Boolean(analysisData),
          score: analysisData ? Number(analysisData.match_score) || 0 : null,
          skills: Array.isArray(resumeData.skills) ? resumeData.skills : [],
          gap: Array.isArray(analysisData?.skill_gaps) ? analysisData.skill_gaps : [],
          prioritySkills: Array.isArray(analysisData?.priority_skills) ? analysisData.priority_skills : [],
          appliedJobId: item.job_id,
          status: statusLabel(item.status, item.hr_decision),
          hrReply: item.hr_reply || "",
          explanation:
            analysisData?.explanation ||
            "此候選尚未執行 AI 分析。建議 HR 先依履歷基本資料初步查看，並請求職者於求職者端完成 AI 分析後，再參考分數與技能缺口。",
        };
      });
      setHrCandidates(candidates);
      setSelectedCandidateId(candidates[0]?.id || null);
      if (list.length === 0) showMessage("此職缺目前尚無投遞候選。", "info");
    } catch (error) {
      console.warn("載入候選失敗：", error.message);
      showMessage("無法載入候選：" + error.message, "warning");
    } finally {
      setLoading(false);
      setLoadingText(null);
    }
  }

  async function openJobsPage() {
    setLoading(true);
    setLoadingText("同步職缺與投遞狀態中...");
    setMessage("");
    try {
      await Promise.all([loadJobs(true), loadFavorites(true), loadMyApplications(true)]);
    } finally {
      setLoading(false);
      setLoadingText(null);
      setPage("jobs");
    }
  }

  async function checkHealth() {
    try {
      await requestJSON("/health");
      setApiStatus("online");
      showMessage("後端 API 連線正常。", "success");
    } catch (error) {
      console.error("健康檢查 API 錯誤：", error);
      setApiStatus("offline");
      showMessage("目前無法連到後端，請確認 FastAPI 是否已啟動。", "warning");
    }
  }

  async function saveResume() {
    if (!validateResumeForSave()) return;

    setLoading(true);
    setLoadingText("儲存履歷中...");
    setMessage("");

    try {
      await requestJSON("/resume", {
        method: "POST",
        body: JSON.stringify(buildResumePayload()),
      });

      setApiStatus("online");
      showMessage("履歷已儲存到資料庫，現在可以進行最新履歷分析。", "success");
      setMode("view");
      await loadMyResume(true);
    } catch (error) {
      console.error("儲存履歷 API 錯誤：", error);
      setApiStatus("offline");
      showMessage(`履歷暫時無法儲存：${error.message}`, "warning");
    } finally {
      setLoading(false);
      setLoadingText(null);
    }
  }

  async function seedJobPosting(job = null) {
    setLoading(true);
    setLoadingText("新增職缺中...");
    setMessage("");

    const payload = buildJobPayload(job || jobRequirement);

    try {
      const data = await requestJSON("/jobs", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setApiStatus("online");
      const newJob = { ...data.data, application_count: 0 };
      setJobList((prev) => {
        const exists = prev.some((j) => j.id === newJob.id);
        return exists ? prev : [newJob, ...prev];
      });
      setSelectedHrJobId(newJob.id);
      showMessage("職缺已新增到後端資料庫，職缺列表已同步更新。", "success");
    } catch (error) {
      console.error("新增職缺 API 錯誤：", error);
      setApiStatus("offline");
      showMessage(`無法新增職缺：${error.message}`, "warning");
    } finally {
      setLoading(false);
      setLoadingText(null);
    }
  }

  function addLocalJob() {
    seedJobPosting();
  }

  async function runAnalysis() {
    if (!validateResumeForSave()) return;

    setLoading(true);
    setLoadingText("AI 正在分析履歷與職缺適配度...");
    setMessage("");

    try {
      const data = await requestJSON("/analyze");
      setApiStatus("online");
      setAnalysis(data);
      setPage("analysis");
    } catch (error) {
      console.error("分析 API 錯誤：", error);
      setApiStatus("offline");
      if (error.message?.includes("401") || error.message?.includes("403")) {
        showMessage("請先登入才能執行分析。", "error");
        return;
      }
      setAnalysis(mockAnalysis);
      setPage("analysis");
      showMessage(`目前顯示前端預覽分析結果：${error.message}`, "warning");
    } finally {
      setLoading(false);
      setLoadingText(null);
    }
  }

  async function loadAnalysisResults() {
    setLoading(true);
    setLoadingText("載入分析紀錄中...");
    setMessage("");

    try {
      const data = await requestJSON("/analysis-results");
      const list = Array.isArray(data) ? data : [];
      setAnalysisHistory(list);
      setApiStatus("online");
      showMessage(list.length > 0 ? `已載入 ${list.length} 筆後端分析紀錄。` : "後端目前沒有分析紀錄。", list.length > 0 ? "success" : "info");
    } catch (error) {
      console.error("分析紀錄 API 錯誤：", error);
      setApiStatus("offline");
      showMessage("目前無法載入後端分析紀錄。", "warning");
    } finally {
      setLoading(false);
      setLoadingText(null);
    }
  }

  async function toggleFavorite(jobId) {
    setFavoriteJobIds((prev) => (prev.includes(jobId) ? prev.filter((id) => id !== jobId) : [...prev, jobId]));
    try {
      const data = await requestJSON("/favorites", {
        method: "POST",
        body: JSON.stringify({ job_id: jobId }),
      });
      if (data?.favorite_job_ids) setFavoriteJobIds(data.favorite_job_ids);
    } catch (error) {
      console.warn("收藏切換失敗：", error.message);
      setFavoriteJobIds((prev) => (prev.includes(jobId) ? prev.filter((id) => id !== jobId) : [...prev, jobId]));
      showMessage("收藏狀態同步失敗：" + error.message, "warning");
    }
  }

  async function applyToJob(job) {
    setLoading(true);
    setLoadingText("確認投遞狀態中...");
    try {
      const latestApplications = await loadMyApplications(true);
      const exists = latestApplications.some((item) => item.jobId === job.id);

      if (exists) {
        showMessage("你已經投遞過這個職缺，可以到投遞紀錄查看 HR 回覆。", "info");
        setPage("applications");
        return;
      }

      setLoadingText("投遞履歷中...");
      await requestJSON("/applications", {
        method: "POST",
        body: JSON.stringify({ job_id: job.id }),
      });
      setApiStatus("online");
      showMessage("已成功投遞！你可以到投遞紀錄查看狀態，HR 也會看到這筆投遞。", "success");
      await loadMyApplications(true);
      setPage("applications");
    } catch (error) {
      console.error("投遞 API 錯誤：", error);
      setApiStatus("offline");
      if (error.message?.includes("409") || error.message?.includes("已經投遞")) {
        showMessage("你已經投遞過這個職缺。", "info");
        await loadMyApplications(true);
        setPage("applications");
      } else {
        showMessage(`投遞失敗：${error.message}`, "error");
      }
    } finally {
      setLoading(false);
      setLoadingText(null);
    }
  }

  async function updateCandidateDecision(candidate, decision) {
    if (!candidate || !candidate.appId) {
      showMessage("此候選沒有對應的投遞紀錄 ID，無法呼叫後端。", "warning");
      return;
    }

    setLoading(true);
    setLoadingText("更新 HR 決定中...");
    const defaultReply =
      decision === "selected"
        ? "您的履歷與此職缺需求相符，後續將進一步聯繫您。"
        : "感謝您的投遞，目前此職缺與您的背景仍有部分落差，建議補強相關技能後再投遞。";

    const hr_reply = hrReplyDraft.trim() || defaultReply;

    try {
      await requestJSON(`/applications/${candidate.appId}/decision`, {
        method: "PUT",
        body: JSON.stringify({ decision, hr_reply }),
      });

      const statusText = decision === "selected" ? "已錄取" : "未錄取";

      setHrCandidates((prev) =>
        prev.map((item) => (item.id === candidate.id ? { ...item, status: statusText, hrReply: hr_reply } : item))
      );

      setHrReplyDraft("");
      setApiStatus("online");
      showMessage(`已將 ${candidate.name} 標記為「${statusText}」，求職者端投遞紀錄將同步更新。`, "success");
    } catch (error) {
      console.error("HR 決定 API 錯誤：", error);
      showMessage(`更新失敗：${error.message}`, "error");
    } finally {
      setLoading(false);
      setLoadingText(null);
    }
  }

  const busyOverlay = <LoadingOverlay show={loading && page !== "login"} title={loadingText || "處理中"} />;

  if (page === "landing") {
    return (
      <AppShell>
        {busyOverlay}
        <div className="mx-auto max-w-7xl">
          <div className="mb-5 flex justify-end">
            <Button variant="secondary" className="px-4 py-2 text-sm" onClick={checkHealth}>
              <Database size={16} /> 檢查 API
            </Button>
          </div>

          <div className="grid gap-10 lg:grid-cols-[1.02fr_0.98fr]">
            <motion.section
              className="grid h-[600px] grid-rows-[auto_1fr_auto] overflow-visible"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55 }}
            >
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm">
                <Briefcase size={16} /> 給求職者與企業 HR 的雙向決策支援
              </div>

              <div className="flex min-h-0 flex-col justify-center pb-3">
                <div>
                  <div className="mb-8 whitespace-nowrap text-5xl font-black leading-none tracking-tight text-slate-950 md:text-6xl xl:text-7xl">
                    X-Ray Resume
                  </div>

                  <h1 className="max-w-3xl text-3xl font-black leading-[1.25] tracking-tight text-slate-900 md:text-4xl xl:text-5xl">
                    看見每個人的可能，
                    <span className="block text-indigo-700">成就更適合的相遇。</span>
                  </h1>

                  <p className="mt-8 max-w-[760px] text-[19px] leading-9 text-slate-600">
                    這是一個可解釋的履歷分析與職缺匹配平台，協助求職者看懂自身優勢、技能缺口與行動方向，也協助企業 HR
                    更有效率地理解候選與職缺需求之間的適配程度。
                  </p>

                  <div className="mt-9 flex flex-wrap gap-4">
                    <Button onClick={() => goLogin("jobseeker")} className="px-8 py-3.5 text-base">
                      求職者入口 <ChevronRight size={19} />
                    </Button>
                    <Button onClick={() => goLogin("hr")} className="px-8 py-3.5 text-base">
                      企業 / HR 入口 <ChevronRight size={19} />
                    </Button>
                  </div>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                {["求職者履歷健檢", "企業 HR 初篩輔助", "推薦依據透明"].map((item) => (
                  <div key={item} className="flex min-h-[50px] items-center gap-2 rounded-2xl bg-white/70 px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm">
                    <CheckCircle2 className="shrink-0 text-emerald-500" size={17} /> {item}
                  </div>
                ))}
              </div>
            </motion.section>

            <motion.section
              className="h-[600px]"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.55, delay: 0.1 }}
            >
              <Card className="flex h-full w-full flex-col p-5 md:p-6">
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-black text-slate-900">平台功能</h2>
                    <p className="mt-1 whitespace-nowrap text-sm text-slate-500">
                      同時支援求職者的履歷優化，以及企業 HR 的候選理解與初步篩選。
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-900 p-3 text-white shadow-lg shadow-indigo-100">
                    <Rocket size={24} />
                  </div>
                </div>

                <div className="grid flex-1 gap-3 sm:grid-cols-2">
                  {featureList.map((feature) => {
                    const Icon = feature.icon;
                    return (
                      <div key={feature.title} className="rounded-3xl border border-slate-100 bg-white/75 p-3.5">
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

          {message && (
            <div className="mt-5">
              <StatusNote type={messageType}>{message}</StatusNote>
            </div>
          )}
        </div>
      </AppShell>
    );
  }

  if (page === "login") {
    const roleLabel = selectedRole === "hr" ? "企業 / HR" : "求職者";

    return (
      <AppShell>
        <div className="mx-auto max-w-xl">
          <Button variant="ghost" onClick={() => setPage("landing")} className="mb-5">
            <ArrowLeft size={16} /> 返回首頁
          </Button>

          <Card className="p-6 md:p-8">
            <div className="mb-7 text-center">
              <div className="mx-auto mb-4 grid h-16 w-16 place-items-center rounded-3xl bg-slate-900 text-white shadow-lg shadow-indigo-100">
                {selectedRole === "hr" ? <Users size={28} /> : <User size={28} />}
              </div>
              <h1 className="text-3xl font-black">{roleLabel}登入</h1>
              <p className="mt-2 text-sm leading-6 text-slate-500">請輸入帳號密碼，登入後資料會與後端同步。</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-5">
              <Field
                label="使用者名稱"
                value={login.username}
                onChange={(v) => setLogin((prev) => ({ ...prev, username: v }))}
                placeholder={selectedRole === "hr" ? "例如：hr_admin" : "例如：jobseeker1"}
              />
              <Field
                label="密碼"
                type="password"
                value={login.password}
                onChange={(v) => setLogin((prev) => ({ ...prev, password: v }))}
                placeholder="請輸入密碼"
              />

              <Button className="w-full py-3 text-base" type="submit" disabled={loading}>
                <Lock size={16} /> {loading ? "登入中..." : "登入"}
              </Button>
            </form>


            <div className="mt-5 flex justify-center gap-3 text-sm">
              <button
                className="cursor-pointer font-semibold text-indigo-700 transition hover:text-indigo-900 hover:underline"
                onClick={() => setSelectedRole(selectedRole === "hr" ? "jobseeker" : "hr")}
              >
                切換成{selectedRole === "hr" ? "求職者" : "企業 / HR"}登入
              </button>
              <span className="text-slate-300">｜</span>
              <button
                className="cursor-pointer font-semibold text-indigo-700 transition hover:text-indigo-900 hover:underline"
                onClick={goRegister}
              >
                註冊帳號
              </button>
            </div>

            {message && (
              <div className="mt-5">
                <StatusNote type={messageType}>{message}</StatusNote>
              </div>
            )}
          </Card>
        </div>
      </AppShell>
    );
  }

  if (page === "register") {
    const roleLabel = selectedRole === "hr" ? "企業 / HR" : "求職者";

    return (
      <AppShell>
        <div className="mx-auto max-w-xl">
          <Button variant="ghost" onClick={() => setPage("login")} className="mb-5">
            <ArrowLeft size={16} /> 返回登入
          </Button>

          <Card className="p-6 md:p-8">
            <div className="mb-7 text-center">
              <div className="mx-auto mb-4 grid h-16 w-16 place-items-center rounded-3xl bg-slate-900 text-white shadow-lg shadow-indigo-100">
                {selectedRole === "hr" ? <Users size={28} /> : <User size={28} />}
              </div>
              <h1 className="text-3xl font-black">{roleLabel}註冊</h1>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                目前先保留註冊介面，Demo 階段暫不開放自行建立帳號。
              </p>
            </div>

            <form onSubmit={handleDemoRegister} className="space-y-5">
              <Field
                label="姓名"
                value={registerForm.display_name}
                onChange={(v) => setRegisterForm((prev) => ({ ...prev, display_name: v }))}
                placeholder="請輸入姓名"
              />
              <Field
                label="使用者名稱"
                value={registerForm.username}
                onChange={(v) => setRegisterForm((prev) => ({ ...prev, username: v }))}
                placeholder={selectedRole === "hr" ? "例如：hr_account" : "例如：jobseeker3"}
              />
              <Field
                label="密碼"
                type="password"
                value={registerForm.password}
                onChange={(v) => setRegisterForm((prev) => ({ ...prev, password: v }))}
                placeholder="請輸入密碼"
              />

              <Button className="w-full py-3 text-base" type="submit">
                <Lock size={16} /> 建立帳號
              </Button>
            </form>

            <div className="mt-5 flex justify-center gap-3 text-sm">
              <button
                className="cursor-pointer font-semibold text-indigo-700 transition hover:text-indigo-900 hover:underline"
                onClick={() => setPage("login")}
              >
                已有帳號，返回登入
              </button>
            </div>

            {message && (
              <div className="mt-5">
                <StatusNote type={messageType}>{message}</StatusNote>
              </div>
            )}
          </Card>
        </div>
      </AppShell>
    );
  }

  if (page === "home") {
    return (
      <AppShell>
        {busyOverlay}
        <div className="mx-auto max-w-7xl">
          <header className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-start">
            <div>
              <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-white/70 px-4 py-2 text-sm font-semibold text-indigo-700 shadow-sm">
                <User size={16} /> 求職者首頁
              </div>
              <h1 className="text-4xl font-black tracking-tight text-slate-950">
                歡迎回來，{currentUser?.display_name || currentUser?.username || resume.full_name}
              </h1>
              <p className="mt-2 text-slate-600">整理履歷、分析職缺適配度，並取得可以實際行動的求職建議。</p>
            </div>
            <TopLogout onLogout={logout} />
          </header>

          <div className="grid gap-5 lg:grid-cols-[1.35fr_0.65fr]">
            <Card className="p-6 md:p-8">
              <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="flex items-center gap-2 text-2xl font-black">
                    <FileText className="text-indigo-600" /> 我的履歷概況
                  </h2>
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
                  <p className="mt-2 text-sm font-semibold leading-6 text-slate-800">{resume.education || "尚未填寫"}</p>
                </div>
                <div className="rounded-3xl bg-white/75 p-5 shadow-sm">
                  <div className="text-xs font-bold uppercase tracking-wide text-slate-400">Target</div>
                  <p className="mt-2 text-sm font-semibold leading-6 text-slate-800">{resume.target_role || "尚未填寫"}</p>
                </div>
                <div className="rounded-3xl bg-white/75 p-5 shadow-sm">
                  <div className="text-xs font-bold uppercase tracking-wide text-slate-400">Salary</div>
                  <p className="mt-2 text-sm font-semibold leading-6 text-slate-800">{resume.expected_salary || "尚未填寫"}</p>
                </div>
              </div>

              <div className="mt-5 rounded-3xl bg-slate-900 p-5 text-white shadow-lg shadow-slate-200">
                <div className="text-sm font-semibold text-white/75">核心技能</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {splitList(resume.skills).length > 0 ? (
                    splitList(resume.skills).map((skill) => (
                      <span key={skill} className="rounded-full bg-white/15 px-3 py-1 text-sm font-semibold backdrop-blur">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-white/70">尚未填寫技能</span>
                  )}
                </div>
              </div>

              <div className="mt-7 flex flex-wrap gap-3">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setMode("view");
                    setPage("resume");
                  }}
                >
                  檢視履歷
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setMode("edit");
                    setPage("resume");
                  }}
                >
                  <Pencil size={16} /> 修改履歷
                </Button>
                <Button onClick={runAnalysis} disabled={loading}>
                  <BarChart3 size={16} /> {loading ? "分析中..." : "開始分析"}
                </Button>
              </div>
            </Card>

            <div className="space-y-5">
              <Card className="p-6">
                <h2 className="flex items-center gap-2 text-xl font-black">
                  <Lightbulb className="text-amber-500" /> 建議流程
                </h2>
                <div className="mt-5 space-y-3">
                  {["確認履歷完整度", "選擇心儀職缺", "查看技能缺口", "確認投遞履歷"].map((step, index) => (
                    <div key={step} className="flex items-center gap-3 rounded-2xl bg-white/75 p-3 text-sm font-semibold text-slate-700">
                      <div className="grid h-8 w-8 place-items-center rounded-xl bg-indigo-50 text-indigo-600">{index + 1}</div>
                      {step}
                    </div>
                  ))}
                </div>
              </Card>

              <Card className="p-6">
                <h2 className="flex items-center gap-2 text-xl font-black">
                  <Briefcase className="text-violet-600" /> 其他功能
                </h2>
                <div className="mt-5 space-y-3">
                  <Button variant="secondary" className="w-full justify-start" onClick={openJobsPage}>
                    職缺推薦
                  </Button>
                  <Button
                    variant="secondary"
                    className="w-full justify-start"
                    onClick={async () => {
                      await loadMyApplications();
                      setPage("applications");
                    }}
                  >
                    投遞紀錄 / HR 回覆
                  </Button>
                  <Button variant="secondary" className="w-full justify-start" onClick={() => setPage("advisor")}>
                    AI 職涯顧問
                  </Button>
                </div>
              </Card>
            </div>
          </div>

          {message && (
            <div className="mt-5">
              <StatusNote type={messageType}>{message}</StatusNote>
            </div>
          )}
        </div>
      </AppShell>
    );
  }

  if (page === "resume") {
    const readOnly = mode === "view";

    return (
      <AppShell>
        {busyOverlay}
        <div className="mx-auto max-w-5xl">
          <TopLogout onLogout={logout} />

          <Button variant="ghost" onClick={() => setPage("home")} className="mb-5">
            <ArrowLeft size={16} /> 返回求職者首頁
          </Button>

          <Card className="p-6 md:p-8">
            <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div>
                <h1 className="text-3xl font-black">{readOnly ? "檢視履歷" : "修改履歷"}</h1>
                <p className="mt-2 text-sm text-slate-500">補齊學歷、技能與職涯目標，能讓後續分析更完整。</p>
              </div>
              <Button variant="secondary" onClick={() => setMode(readOnly ? "edit" : "view")}>
                {readOnly ? "切換成修改" : "切換成檢視"}
              </Button>
            </div>

            <div className="mb-5 rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">
              <span className="text-rose-500">*</span> 為必填欄位；姓名依登入帳號帶入，避免投遞履歷時與帳號資料不一致。
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <Field label="姓名" value={resume.full_name} onChange={(v) => setResumeField("full_name", v)} disabled helpText="姓名由帳號資料帶入，不開放在履歷頁修改。" />
              <Field label="目標職位" value={resume.target_role} onChange={(v) => setResumeField("target_role", v)} disabled={readOnly} required />
              <Field label="學歷" value={resume.education} onChange={(v) => setResumeField("education", v)} multiline disabled={readOnly} required />
              <Field label="技能 (,分隔)" value={resume.skills} onChange={(v) => setResumeField("skills", v)} multiline disabled={readOnly} required />
              <Field label="證照" value={resume.certifications} onChange={(v) => setResumeField("certifications", v)} multiline disabled={readOnly} helpText="選填，可填 AWS、Google、語言檢定等證照。" />
              <Field label="獎項 / 其他加分項" value={resume.awards} onChange={(v) => setResumeField("awards", v)} multiline disabled={readOnly} helpText="選填，可填競賽、社團、志工、作品亮點。" />
              <Field label="期望薪資" value={resume.expected_salary} onChange={(v) => setResumeField("expected_salary", v)} disabled={readOnly} required />
            </div>

            <div className="mt-7 flex flex-wrap gap-3">
              <Button onClick={saveResume} disabled={loading || readOnly}>
                <Save size={16} /> {loading ? "儲存中..." : "儲存變更"}
              </Button>
              <Button variant="secondary" onClick={runAnalysis} disabled={loading}>
                <BarChart3 size={16} /> 查看分析
              </Button>
            </div>

            {message && (
              <div className="mt-5">
                <StatusNote type={messageType}>{message}</StatusNote>
              </div>
            )}
          </Card>
        </div>
      </AppShell>
    );
  }

  if (page === "analysis") {
    const shapValues = analysis?.shap_values || {};
    const shapItems = [
      { label: "技能匹配度", value: shapValues.skill_match },
      { label: "學歷符合度", value: shapValues.education },
      { label: "工作經驗", value: shapValues.experience },
      { label: "專案作品", value: shapValues.projects },
    ].filter((item) => item.value !== undefined && item.value !== null);

    return (
      <AppShell>
        {busyOverlay}
        <div className="mx-auto max-w-7xl">
          <TopLogout onLogout={logout} />

          <Button variant="ghost" onClick={() => setPage("home")} className="mb-5">
            <ArrowLeft size={16} /> 返回求職者首頁
          </Button>

          {message && (
            <div className="mb-5">
              <StatusNote type={messageType}>{message}</StatusNote>
            </div>
          )}

          <div className="grid gap-5 lg:grid-cols-[0.78fr_1.22fr]">
            <Card className="grid place-items-center p-7 text-center">
              <ScoreRing score={analysis?.match_score ?? 0} />
              <h1 className="mt-6 text-3xl font-black">履歷分析報告</h1>
              <p className="mt-2 text-sm text-slate-500">目標職缺：{analysis?.job_snapshot?.title || "推薦職缺"}</p>
              <div className="mt-5 flex flex-wrap justify-center gap-2">
                {(analysis?.job_snapshot?.required_skills || []).map((skill) => (
                  <span key={skill} className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">
                    {skill}
                  </span>
                ))}
              </div>
            </Card>

            <Card className="p-6 md:p-8">
              <h2 className="flex items-center gap-2 text-2xl font-black">
                <ShieldCheck className="text-emerald-500" /> 為什麼這樣推薦？
              </h2>
              <p className="mt-4 whitespace-pre-line rounded-3xl bg-white/75 p-5 text-sm leading-7 text-slate-700 shadow-sm">
                {analysis?.scenario_simulation || "目前正在整理分析結果。"}
              </p>
            </Card>
          </div>

          {shapItems.length > 0 && (
            <Card className="mt-5 p-6 md:p-8">
              <h2 className="flex items-center gap-2 text-2xl font-black">
                <BarChart3 className="text-indigo-600" /> 權重解釋
              </h2>
              <div className="mt-5 grid gap-4 md:grid-cols-4">
                {shapItems.map((item) => {
                  const percent = Math.round(Number(item.value) * 100);
                  return (
                    <div key={item.label} className="rounded-3xl bg-white/75 p-5 shadow-sm">
                      <div className="text-sm font-bold text-slate-700">{item.label}</div>
                      <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-100">
                        <div className="h-full rounded-full bg-indigo-600" style={{ width: `${Math.max(4, percent)}%` }} />
                      </div>
                      <div className="mt-3 text-2xl font-black text-slate-900">{percent}%</div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          <div className="mt-5 grid gap-5 lg:grid-cols-3">
            <Card className="p-6 lg:col-span-2">
              <h2 className="flex items-center gap-2 text-2xl font-black">
                <Rocket className="text-violet-600" /> 優先補強技能
              </h2>
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
              <h2 className="flex items-center gap-2 text-2xl font-black">
                <TrendingUp className="text-sky-600" /> 薪資影響
              </h2>
              <p className="mt-4 whitespace-pre-line rounded-3xl bg-white/75 p-5 text-sm leading-7 text-slate-700 shadow-sm">
                {analysis?.salary_impact || "目前正在整理薪資影響。"}
              </p>
            </Card>
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <Button variant="secondary" onClick={openJobsPage}>
              查看可投遞職缺
            </Button>
            <Button variant="secondary" onClick={() => setPage("scenario")}>
              情境模擬
            </Button>
            <Button onClick={() => setPage("resume")}>回去優化履歷</Button>
          </div>
        </div>
      </AppShell>
    );
  }

  if (page === "jobs") {
    return (
      <AppShell>
        {busyOverlay}
        <div className="mx-auto max-w-7xl">
          <TopLogout onLogout={logout} />

          <Button variant="ghost" onClick={() => setPage("home")} className="mb-5">
            <ArrowLeft size={16} /> 返回求職者首頁
          </Button>

          <Card className="p-6 md:p-8">
            <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div>
                <h1 className="flex items-center gap-3 text-3xl font-black">
                  <Briefcase className="text-indigo-600" /> 職缺推薦
                </h1>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  可收藏心儀職缺，確認後投遞。
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button variant="secondary" onClick={openJobsPage} disabled={loading}>
                  <RefreshCw size={16} /> 重新整理
                </Button>
                <Button variant="secondary" onClick={() => setPage("applications")}>
                  查看投遞紀錄
                </Button>
              </div>
            </div>

            <div className="grid gap-5 lg:grid-cols-3">
              {jobList.length === 0 ? (
                <div className="lg:col-span-3">
                  <StatusNote type="info">目前尚無後端職缺資料，請確認 HR 是否已新增職缺，或重新整理職缺列表。</StatusNote>
                </div>
              ) : (
                jobList.map((job) => {
                  const isFavorite = favoriteJobIds.includes(job.id);
                  const hasApplied = applications.some((item) => item.jobId === job.id);
                  const isAnalyzedJob = Boolean(analysis?.job_snapshot?.title && analysis.job_snapshot.title === job.title);
                  const level = isAnalyzedJob ? getScoreLevel(analysis.match_score) : null;

                  return (
                    <div key={job.id} className="rounded-3xl border border-slate-100 bg-white/75 p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-lg">
                      <div className="mb-4 flex items-center justify-between gap-3">
                        {isAnalyzedJob ? (
                          <>
                            <span className={`rounded-full border px-3 py-1 text-xs font-bold ${level.className}`}>{level.label}</span>
                            <span className="rounded-2xl bg-slate-900 px-3 py-2 text-sm font-black text-white">{analysis.match_score}</span>
                          </>
                        ) : (
                          <>
                            <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-bold text-slate-600">開放投遞</span>
                            <span className="rounded-2xl bg-indigo-50 px-3 py-2 text-xs font-black text-indigo-700">尚未分析</span>
                          </>
                        )}
                      </div>
                      <h2 className="text-xl font-black text-slate-900">{job.title}</h2>
                      <p className="mt-1 text-sm font-semibold text-slate-500">{job.company}</p>
                      <p className="mt-3 text-sm leading-6 text-slate-600">{job.description}</p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {(job.required_skills || []).map((skill) => (
                          <span key={skill} className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">
                            {skill}
                          </span>
                        ))}
                      </div>
                      <div className="mt-4 rounded-2xl bg-slate-50 p-3 text-sm font-semibold text-slate-600">
                        {job.salary_range || "薪資未提供"} · 最低年資 {job.min_experience ?? 0} 年
                      </div>
                      <div className="mt-5 flex flex-wrap gap-2">
                        <Button variant={isFavorite ? "soft" : "secondary"} onClick={() => toggleFavorite(job.id)}>
                          {isFavorite ? "已加入心儀" : "加入心儀"}
                        </Button>
                        <Button onClick={() => applyToJob(job)} disabled={hasApplied || loading}>
                          <Send size={16} /> {hasApplied ? "已投遞" : "確認投遞"}
                        </Button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </Card>

          {message && (
            <div className="mt-5">
              <StatusNote type={messageType}>{message}</StatusNote>
            </div>
          )}
        </div>
      </AppShell>
    );
  }

  if (page === "applications") {
    return (
      <AppShell>
        {busyOverlay}
        <div className="mx-auto max-w-6xl">
          <TopLogout onLogout={logout} />

          <Button variant="ghost" onClick={() => setPage("home")} className="mb-5">
            <ArrowLeft size={16} /> 返回求職者首頁
          </Button>

          <Card className="p-6 md:p-8">
            <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div>
                <h1 className="flex items-center gap-3 text-3xl font-black">
                  <ClipboardList className="text-indigo-600" /> 投遞紀錄 / HR 回覆
                </h1>
                <p className="mt-2 text-sm leading-6 text-slate-500">求職者可以查看已投遞職缺、目前狀態，以及 HR 的回覆內容。</p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button variant="secondary" onClick={() => loadMyApplications()} disabled={loading}>
                  <RefreshCw size={16} /> {loading ? "載入中..." : "重新整理"}
                </Button>
                <Button variant="secondary" onClick={openJobsPage}>
                  繼續查看職缺
                </Button>
              </div>
            </div>

            <div className="space-y-4">
              {applications.length === 0 ? (
                <StatusNote>目前尚未投遞任何職缺。</StatusNote>
              ) : (
                applications.map((item) => (
                  <div key={item.id} className="rounded-3xl border border-slate-100 bg-white/75 p-5 shadow-sm">
                    <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
                      <div>
                        <h2 className="text-xl font-black text-slate-900">{item.jobTitle}</h2>
                        <p className="mt-1 text-sm font-semibold text-slate-500">
                          {item.company} · {item.createdAt}
                        </p>
                      </div>
                      <span className="rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">{item.status}</span>
                    </div>
                    <p className="mt-4 rounded-3xl bg-slate-50 p-4 text-sm leading-7 text-slate-700">{item.reply}</p>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </AppShell>
    );
  }

  if (page === "hr") {
    return (
      <AppShell>
        {busyOverlay}
        <div className="mx-auto max-w-7xl">
          <header className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-start">
            <div>
              <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-white/70 px-4 py-2 text-sm font-semibold text-indigo-700 shadow-sm">
                <Users size={16} /> HR 招募管理
              </div>
              <h1 className="text-4xl font-black tracking-tight text-slate-950">職缺與投遞履歷管理</h1>
              <p className="mt-2 text-slate-600">可新增多個職缺、查看職缺列表，並點進各職缺檢視投遞候選。</p>
            </div>
            <TopLogout onLogout={logout} />
          </header>

          <div className="grid gap-5 md:grid-cols-3">
            <MiniMetric label="職缺數" value={jobList.length} icon={Briefcase} />
            <MiniMetric label="總投遞數" value={candidateStats.total} icon={Users} />
            <MiniMetric label="中高適配" value={candidateStats.high + candidateStats.medium} icon={BarChart3} />
          </div>

          <div className="mt-5 grid gap-5 lg:grid-cols-[0.85fr_1.15fr]">
            <Card className="p-6 md:p-8">
              <h2 className="flex items-center gap-2 text-2xl font-black">
                <Briefcase className="text-indigo-600" /> 新增職缺
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">填寫職缺資料後，直接同步新增到後端資料庫。</p>

              <div className="mt-6 grid gap-5">
                <Field label="公司名稱" value={jobRequirement.company} onChange={(v) => setJobField("company", v)} />
                <Field label="職缺名稱" value={jobRequirement.title} onChange={(v) => setJobField("title", v)} />
                <Field label="需求技能，逗號分隔" value={jobRequirement.required_skills} onChange={(v) => setJobField("required_skills", v)} multiline />
                <div className="grid gap-5 md:grid-cols-2">
                  <Field label="薪資範圍" value={jobRequirement.salary_range} onChange={(v) => setJobField("salary_range", v)} />
                  <Field label="最低年資" value={jobRequirement.min_experience} onChange={(v) => setJobField("min_experience", v)} type="number" />
                </div>
                <Field label="職缺描述" value={jobRequirement.description} onChange={(v) => setJobField("description", v)} multiline />
              </div>

              <div className="mt-7 flex flex-wrap gap-3">
                <Button onClick={addLocalJob} disabled={loading}>
                  <Save size={16} /> {loading ? "新增中..." : "新增職缺到後端"}
                </Button>
                <Button variant="secondary" onClick={() => loadHrJobs()} disabled={loading}>
                  <RefreshCw size={16} /> 重新載入職缺列表
                </Button>
              </div>
            </Card>

            <Card className="p-6 md:p-8">
              <h2 className="flex items-center gap-2 text-2xl font-black">
                <ClipboardList className="text-violet-600" /> 職缺列表
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">點選職缺後，會進入該職缺頁面查看投遞候選。</p>

              <div className="mt-5 space-y-3">
                {jobList.length === 0 ? (
                  <StatusNote type="info">目前尚無職缺，請先新增一個職缺。</StatusNote>
                ) : (
                  jobList.map((job) => (
                    <button
                      key={job.id}
                      onClick={() => {
                        setSelectedHrJobId(job.id);
                        setSelectedCandidateId(null);
                        setHrCandidates([]);
                        setHrReplyDraft("");
                        setPage("hrJobDetail");
                        loadJobApplications(job.id);
                      }}
                      className="w-full cursor-pointer rounded-3xl border border-slate-100 bg-white/75 p-4 text-left transition hover:-translate-y-0.5 hover:border-indigo-200 hover:bg-indigo-50/60 hover:shadow-lg"
                    >
                      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
                        <div>
                          <div className="text-lg font-black text-slate-900">{job.title}</div>
                          <div className="mt-1 text-sm text-slate-500">
                            {job.company} · {job.salary_range}
                          </div>
                        </div>
                        <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-bold text-slate-600">
                          {job.application_count ?? 0} 位投遞
                        </span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </Card>
          </div>

          {message && (
            <div className="mt-5">
              <StatusNote type={messageType}>{message}</StatusNote>
            </div>
          )}
        </div>
      </AppShell>
    );
  }

  if (page === "hrJobDetail") {
    return (
      <AppShell>
        {busyOverlay}
        <div className="mx-auto max-w-7xl">
          <TopLogout onLogout={logout} />

          <Button variant="ghost" onClick={() => setPage("hr")} className="mb-5">
            <ArrowLeft size={16} /> 返回職缺列表
          </Button>

          <Card className="p-6 md:p-8">
            <div className="flex flex-col justify-between gap-5 md:flex-row md:items-start">
              <div>
                <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-indigo-50 px-4 py-2 text-sm font-semibold text-indigo-700">
                  <Briefcase size={16} /> 職缺詳細資料
                </div>
                <h1 className="text-3xl font-black text-slate-950">{selectedHrJob?.title}</h1>
                <p className="mt-2 text-sm font-semibold text-slate-500">
                  {selectedHrJob?.company} · {selectedHrJob?.salary_range}
                </p>
                <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600">{selectedHrJob?.description}</p>
              </div>

              <div className="rounded-3xl bg-slate-900 px-5 py-4 text-white shadow-lg shadow-slate-200">
                <div className="text-3xl font-black">{candidatesForSelectedJob.length}</div>
                <div className="text-xs font-semibold text-white/70">投遞候選</div>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              {(selectedHrJob?.required_skills || []).map((skill) => (
                <span key={skill} className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">
                  {skill}
                </span>
              ))}
            </div>

            <div className="mt-7 flex flex-wrap gap-3">
              <Button variant="secondary" onClick={() => loadJobApplications(selectedHrJob?.id)} disabled={loading || !selectedHrJob}>
                <RefreshCw size={16} /> {loading ? "載入中..." : "重新載入候選"}
              </Button>
              <Button variant="secondary" onClick={() => setPage("hr")}>
                管理其他職缺
              </Button>
            </div>
          </Card>

          <Card className="mt-5 p-6 md:p-8">
            <h2 className="flex items-center gap-2 text-2xl font-black">
              <Users className="text-indigo-600" /> 投遞到此職缺的候選
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">點選候選後，可查看適配分數、推薦原因與技能缺口。</p>

            <div className="mt-5 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
              <div className="space-y-3">
                {candidatesForSelectedJob.length === 0 ? (
                  <StatusNote>目前此職缺尚無投遞候選。</StatusNote>
                ) : (
                  candidatesForSelectedJob.map((candidate) => {
                    const level = candidate.hasAnalysis ? getScoreLevel(candidate.score) : null;
                    const active = selectedCandidate?.id === candidate.id;

                    return (
                      <button
                        key={candidate.id}
                        onClick={() => {
                          setSelectedCandidateId(candidate.id);
                          setHrReplyDraft(candidate.hrReply || "");
                        }}
                        className={`w-full cursor-pointer rounded-3xl border p-4 text-left transition hover:-translate-y-0.5 hover:shadow-lg ${
                          active ? "border-indigo-200 bg-indigo-50/80 shadow-lg shadow-indigo-100" : "border-slate-100 bg-white/75 hover:bg-white"
                        }`}
                      >
                        <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
                          <div>
                            <div className="text-lg font-black text-slate-900">{candidate.name}</div>
                            <div className="mt-1 text-sm text-slate-500">{candidate.target}</div>
                          </div>
                          <div className="flex items-center gap-2">
                            {candidate.hasAnalysis ? (
                              <>
                                <span className={`rounded-full border px-3 py-1 text-xs font-bold ${level.className}`}>{level.label}</span>
                                <span className="rounded-2xl bg-slate-900 px-3 py-2 text-sm font-black text-white">{candidate.score}</span>
                              </>
                            ) : (
                              <span className="rounded-full border border-amber-100 bg-amber-50 px-3 py-1 text-xs font-bold text-amber-700">尚未分析</span>
                            )}
                          </div>
                        </div>

                        <div className="mt-3 inline-flex rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-bold text-slate-600">{candidate.status}</div>
                      </button>
                    );
                  })
                )}
              </div>

              {selectedCandidate ? (
                <div className="rounded-3xl border border-slate-100 bg-white/75 p-5 shadow-sm">
                  <div className="flex flex-col justify-between gap-5 md:flex-row md:items-start">
                    <div>
                      <h3 className="text-2xl font-black">{selectedCandidate.name} 的分析摘要</h3>
                      <p className="mt-2 whitespace-pre-line text-sm leading-7 text-slate-600">{selectedCandidate.explanation}</p>
                    </div>
                    {selectedCandidate.hasAnalysis ? (
                      <ScoreRing score={selectedCandidate.score} />
                    ) : (
                      <div className="rounded-3xl border border-amber-100 bg-amber-50 px-5 py-4 text-center text-amber-700">
                        <div className="text-2xl font-black">尚未分析</div>
                      </div>
                    )}
                  </div>

                  <div className="mt-6 grid gap-5 md:grid-cols-2">
                    <div className="rounded-3xl bg-slate-50 p-5">
                      <h4 className="font-black text-slate-900">已具備技能</h4>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(selectedCandidate.skills || []).length > 0 ? (
                          selectedCandidate.skills.map((skill) => (
                            <span key={skill} className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                              {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-slate-500">後端目前未提供履歷技能快照。</span>
                        )}
                      </div>
                    </div>

                    <div className="rounded-3xl bg-slate-50 p-5">
                      <h4 className="font-black text-slate-900">缺口 / 可追問項目</h4>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(selectedCandidate.gap || []).length > 0 ? (
                          selectedCandidate.gap.map((skill) => (
                            <span key={skill} className="rounded-full bg-amber-50 px-3 py-1 text-xs font-bold text-amber-700">
                              {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-slate-500">尚未有 AI 技能缺口資料。</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 rounded-3xl border border-slate-100 bg-slate-50 p-5">
                    <h4 className="font-black text-slate-900">HR 回覆意見，選填</h4>
                    <p className="mt-1 text-sm leading-6 text-slate-500">可直接選擇或拒絕；若有填寫意見，求職者端投遞紀錄會看到這段回覆。</p>
                    <textarea
                      value={hrReplyDraft}
                      onChange={(e) => setHrReplyDraft(e.target.value)}
                      rows={4}
                      className="mt-4 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100"
                      placeholder="例如：您的後端基礎符合需求，建議補充雲端部署作品後安排下一步。"
                    />
                    <div className="mt-4 flex flex-wrap gap-3">
                      <Button variant="success" onClick={() => updateCandidateDecision(selectedCandidate, "selected")} disabled={loading}>
                        <CheckCircle2 size={16} /> {loading ? "更新中..." : "選擇"}
                      </Button>
                      <Button variant="danger" onClick={() => updateCandidateDecision(selectedCandidate, "rejected")} disabled={loading}>
                        {loading ? "更新中..." : "拒絕"}
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <StatusNote>請先選擇一位候選查看分析摘要。</StatusNote>
              )}
            </div>
          </Card>

          {message && (
            <div className="mt-5">
              <StatusNote type={messageType}>{message}</StatusNote>
            </div>
          )}
        </div>
      </AppShell>
    );
  }

  if (page === "advisor" || page === "scenario") {
    const pageInfo = {
      advisor: {
        title: "AI 職涯顧問",
        icon: Lightbulb,
        description: "先用靜態建議呈現聊天機器人區塊，之後可接 LLM 或問答 API。",
        cards: [
          { title: "履歷建議", subtitle: "優先補強", text: "請在專案經驗中加入具體成果，例如效能提升比例、使用者數、部署環境。" },
          { title: "學習建議", subtitle: "未來 3 個月", text: "建議完成 Redis 快取實作、Kubernetes 部署，以及一個高併發後端小專案。" },
          { title: "面試準備", subtitle: "系統設計", text: "可以練習短網址服務、排隊系統、推薦系統等常見系統設計題。" },
        ],
      },
      scenario: {
        title: "情境模擬",
        icon: Compass,
        description: "先以前端模擬方式呈現「如果我學會某技能」的結果，之後可由後端 AI 模型回傳新版分數。",
        cards: [
          { title: "如果我學會 Kubernetes", subtitle: "+10 分", text: "可提升雲端部署與服務維運相關職缺的競爭力。" },
          { title: "如果我學會 Redis", subtitle: "+7 分", text: "可補強快取、高併發與後端效能優化能力。" },
          { title: "如果我完成系統設計專案", subtitle: "+8 分", text: "可提升資深後端職缺的架構思考與可解釋加分項。" },
        ],
      },
    }[page];

    const Icon = pageInfo.icon;

    return (
      <AppShell>
        {busyOverlay}
        <div className="mx-auto max-w-6xl">
          <TopLogout onLogout={logout} />

          <Button variant="ghost" onClick={() => setPage("home")} className="mb-5">
            <ArrowLeft size={16} /> 返回求職者首頁
          </Button>

          <Card className="p-6 md:p-8">
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div>
                <h1 className="flex items-center gap-3 text-3xl font-black">
                  <Icon className="text-indigo-600" /> {pageInfo.title}
                </h1>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{pageInfo.description}</p>
              </div>
              <div className="rounded-2xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-700">
                <AlertCircle className="mr-2 inline" size={16} /> 前端預留功能
              </div>
            </div>

            <div className="mt-7 grid gap-5 md:grid-cols-3">
              {pageInfo.cards.map((card) => (
                <div key={card.title} className="rounded-3xl border border-slate-100 bg-white/75 p-5 shadow-sm">
                  <div className="text-xs font-bold uppercase tracking-wide text-indigo-600">{card.subtitle}</div>
                  <h2 className="mt-2 text-xl font-black text-slate-900">{card.title}</h2>
                  <p className="mt-3 text-sm leading-6 text-slate-500">{card.text}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </AppShell>
    );
  }

  return null;
}
