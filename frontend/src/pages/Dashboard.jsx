import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
        Activity, DollarSign, TrendingDown, AlertCircle,
        CheckCircle, BarChart2, FileText, RefreshCw, ShieldCheck,
        User, Building2,
} from "lucide-react";
import UploadSection from "../components/UploadSection";
import AnalysisProgress from "../components/AnalysisProgress";
import ResultsPanel from "../components/ResultsPanel";
import PricingSummary from "../components/PricingSummary";
import AppealDownload from "../components/AppealDownload";
import Chatbot from "../components/Chatbot";
import LanguageSelector from "../components/LanguageSelector";
import { auditBill } from "../services/api";
import { getT } from "../services/translations";


/* ── Stat card ──────────────────────────────────────────────── */
const Stat = ({ icon: Icon, label, value, sub, accent }) => (
        <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                className="card card-hover p-5"
        >
                <div className={`inline-flex p-2.5 rounded-xl border mb-4 ${accent.wrap}`}>
                        <Icon className={`w-5 h-5 ${accent.icon}`} />
                </div>
                <p className="text-[11px] font-bold uppercase tracking-widest text-slate-500">{label}</p>
                <p className={`text-2xl font-extrabold mt-1 tracking-tight ${accent.val}`}>{value}</p>
                {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
        </motion.div>
);


/* ── Circular score meter ───────────────────────────────────── */
const Ring = ({ score, label, color }) => {
        const r = 28, circ = 2 * Math.PI * r;
        return (
                <div className="flex flex-col items-center gap-2">
                        <div className="relative w-20 h-20">
                                <svg className="-rotate-90 w-20 h-20">
                                        <circle cx="40" cy="40" r={r} stroke="#0a1628" strokeWidth="5" fill="none" />
                                        <motion.circle
                                                cx="40" cy="40" r={r}
                                                stroke={color} strokeWidth="5" fill="none"
                                                strokeLinecap="round"
                                                strokeDasharray={circ}
                                                initial={{ strokeDashoffset: circ }}
                                                animate={{ strokeDashoffset: circ * (1 - score) }}
                                                transition={{ duration: 1.2, ease: "easeOut" }}
                                        />
                                </svg>
                                <div className="absolute inset-0 flex items-center justify-center">
                                        <span className="text-base font-extrabold text-white">
                                                {Math.round(score * 100)}%
                                        </span>
                                </div>
                        </div>
                        <p className="text-[11px] text-slate-500 font-medium text-center leading-tight max-w-[80px]">{label}</p>
                </div>
        );
};


/* ── Tabs ───────────────────────────────────────────────────── */
const TAB_IDS = [
        { id: "issues", Icon: AlertCircle },
        { id: "pricing", Icon: BarChart2 },
        { id: "appeal", Icon: FileText },
];


/* ── Main Dashboard ─────────────────────────────────────────── */
export default function Dashboard() {
        const [result, setResult] = useState(null);
        const [loading, setLoading] = useState(false);
        const [error, setError] = useState(null);
        const [tab, setTab] = useState("issues");
        const [language, setLanguage] = useState("en");

        const t = getT(language);
        const TABS = TAB_IDS.map(({ id, Icon }) => ({ id, Icon, label: t.tabs[id] }));

        const handleSubmit = async (files) => {
                setLoading(true); setError(null); setResult(null);
                try {
                        setResult(await auditBill(files));
                        setTab("issues");
                } catch (e) { setError(e.message); }
                finally { setLoading(false); }
        };

        const reset = () => { setResult(null); setError(null); };

        const bill = result?.extracted_bill;

        return (
                <div className="min-h-screen">

                        {/* ── Navbar ── */}
                        <nav className="sticky top-0 z-50 border-b border-[#1e3a5f]/40
                      bg-[#060d1a]/90 backdrop-blur-xl">
                                <div className="max-w-6xl mx-auto px-4 sm:px-6 h-15 flex items-center justify-between py-3">
                                        <div className="flex items-center gap-3">
                                                <div className="p-2 bg-blue-500/15 rounded-xl border border-blue-500/20">
                                                        <Activity className="w-4.5 h-4.5 text-blue-400" style={{ width: 18, height: 18 }} />
                                                </div>
                                                <div className="flex items-baseline gap-2">
                                                        <span className="font-extrabold text-white text-lg tracking-tight">MedAudit</span>
                                                        <span className="text-xs text-slate-600 font-medium hidden sm:block">{t.nav.tagline}</span>
                                                </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                                <LanguageSelector language={language} onChange={setLanguage} />
                                                {result && (
                                                        <button onClick={reset} className="btn-ghost flex items-center gap-1.5 text-sm">
                                                                <RefreshCw className="w-3.5 h-3.5" /> {t.nav.newAudit}
                                                        </button>
                                                )}
                                        </div>
                                </div>
                        </nav>

                        <main className="max-w-6xl mx-auto px-4 sm:px-6 py-10 space-y-8">

                                {/* ── Hero (only pre-results) ── */}
                                <AnimatePresence>
                                        {!result && !loading && (
                                                <motion.div
                                                        key="hero"
                                                        initial={{ opacity: 0, y: -12 }}
                                                        animate={{ opacity: 1, y: 0 }}
                                                        exit={{ opacity: 0, y: -12 }}
                                                        className="text-center space-y-4"
                                                >
                                                        <div className="inline-flex items-center gap-2 border border-blue-500/25
                              bg-blue-500/8 rounded-full px-4 py-1.5">
                                                                <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                                                                <span className="text-xs font-semibold text-blue-400 tracking-wide">
                                                                        {t.hero.badge}
                                                                </span>
                                                        </div>
                                                        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
                                                                {t.hero.heading1}<br />
                                                                <span className="bg-gradient-to-r from-blue-400 via-blue-300 to-cyan-400
                                 bg-clip-text text-transparent">
                                                                        {t.hero.heading2}
                                                                </span>
                                                        </h1>
                                                        <p className="text-slate-500 max-w-md mx-auto text-base leading-relaxed">
                                                                {t.hero.subtext}
                                                        </p>
                                                </motion.div>
                                        )}
                                </AnimatePresence>

                                {/* ── Upload ── */}
                                <AnimatePresence mode="wait">
                                        {!result && !loading && (
                                                <motion.div key="upload" exit={{ opacity: 0, y: -16 }}>
                                                        <UploadSection onSubmit={handleSubmit} isLoading={loading} language={language} />
                                                </motion.div>
                                        )}
                                </AnimatePresence>

                                {/* ── Progress ── */}
                                <AnimatePresence>
                                        {loading && (
                                                <motion.div key="progress" exit={{ opacity: 0 }}>
                                                        <AnalysisProgress isActive={loading} language={language} />
                                                </motion.div>
                                        )}
                                </AnimatePresence>

                                {/* ── Error ── */}
                                <AnimatePresence>
                                        {error && (
                                                <motion.div
                                                        key="error"
                                                        initial={{ opacity: 0, scale: 0.97 }}
                                                        animate={{ opacity: 1, scale: 1 }}
                                                        exit={{ opacity: 0 }}
                                                        className="max-w-xl mx-auto card border-red-500/20 bg-red-500/5 p-6"
                                                >
                                                        <div className="flex items-start gap-3">
                                                                <div className="p-2 bg-red-500/15 rounded-xl border border-red-500/20">
                                                                        <AlertCircle className="w-5 h-5 text-red-400" />
                                                                </div>
                                                                <div>
                                                                        <h3 className="font-bold text-white">{t.error.title}</h3>
                                                                        <p className="text-sm text-slate-400 mt-1 leading-relaxed">{error}</p>
                                                                        <button onClick={reset} className="btn-primary mt-4 text-sm px-4 py-2">
                                                                                {t.error.retry}
                                                                        </button>
                                                                </div>
                                                        </div>
                                                </motion.div>
                                        )}
                                </AnimatePresence>

                                {/* ── Results ── */}
                                <AnimatePresence>
                                        {result && (
                                                <motion.div
                                                        key="results"
                                                        initial={{ opacity: 0, y: 20 }}
                                                        animate={{ opacity: 1, y: 0 }}
                                                        className="space-y-6"
                                                >
                                                        {/* ── Stat grid ── */}
                                                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                                                <Stat icon={DollarSign} label={t.stats.charged}
                                                                        value={`$${result.total_billed.toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
                                                                        accent={{ wrap: "bg-slate-700/40 border-slate-600/40", icon: "text-slate-300", val: "text-white" }} />
                                                                <Stat icon={CheckCircle} label={t.stats.fair}
                                                                        value={`$${result.estimated_fair_total.toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
                                                                        accent={{ wrap: "bg-emerald-500/15 border-emerald-500/25", icon: "text-emerald-400", val: "text-emerald-400" }} />
                                                                <Stat icon={TrendingDown} label={t.stats.savings}
                                                                        value={`$${result.estimated_savings.toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
                                                                        sub={result.estimated_savings > 0 ? t.stats.overcharged : t.stats.no_overcharge}
                                                                        accent={{
                                                                                wrap: "bg-red-500/15 border-red-500/25", icon: "text-red-400",
                                                                                val: result.estimated_savings > 0 ? "text-red-400" : "text-emerald-400"
                                                                        }} />
                                                                <Stat icon={AlertCircle} label={t.stats.issues}
                                                                        value={result.issue_count}
                                                                        sub={`${result.pricing_results.filter(p => p.is_flagged).length} ${t.stats.flagged_prices}`}
                                                                        accent={{
                                                                                wrap: result.issue_count > 0 ? "bg-amber-500/15 border-amber-500/25" : "bg-emerald-500/15 border-emerald-500/25",
                                                                                icon: result.issue_count > 0 ? "text-amber-400" : "text-emerald-400",
                                                                                val: "text-white"
                                                                        }} />
                                                        </div>

                                                        {/* ── Score rings ── */}
                                                        <motion.div
                                                                initial={{ opacity: 0, y: 16 }}
                                                                animate={{ opacity: 1, y: 0 }}
                                                                transition={{ delay: 0.2 }}
                                                                className="card p-6"
                                                        >
                                                                <p className="section-label mb-5">{t.scores.title}</p>
                                                                <div className="flex justify-around flex-wrap gap-6">
                                                                        <Ring score={result.overall_confidence} label={t.scores.confidence} color="#3b82f6" />
                                                                        <Ring score={result.risk_score} label={t.scores.risk} color="#ef4444" />
                                                                        <Ring score={result.appeal_success_probability} label={t.scores.appeal} color="#22c55e" />
                                                                </div>
                                                        </motion.div>

                                                        {/* ── Patient / Provider bar ── */}
                                                        {(bill?.patient_name || bill?.provider_name) && (
                                                                <motion.div
                                                                        initial={{ opacity: 0, y: 16 }}
                                                                        animate={{ opacity: 1, y: 0 }}
                                                                        transition={{ delay: 0.22 }}
                                                                        className="card px-5 py-3 flex flex-wrap items-center gap-x-8 gap-y-3"
                                                                >
                                                                        {bill.patient_name && (
                                                                                <div className="flex items-center gap-2.5">
                                                                                        <div className="p-1.5 bg-blue-500/10 rounded-lg border border-blue-500/20">
                                                                                                <User className="w-3.5 h-3.5 text-blue-400" />
                                                                                        </div>
                                                                                        <div>
                                                                                                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{t.info.patient}</p>
                                                                                                <p className="text-sm font-semibold text-white">{bill.patient_name}</p>
                                                                                        </div>
                                                                                </div>
                                                                        )}
                                                                        {bill.provider_name && (
                                                                                <div className="flex items-center gap-2.5">
                                                                                        <div className="p-1.5 bg-purple-500/10 rounded-lg border border-purple-500/20">
                                                                                                <Building2 className="w-3.5 h-3.5 text-purple-400" />
                                                                                        </div>
                                                                                        <div>
                                                                                                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{t.info.provider}</p>
                                                                                                <p className="text-sm font-semibold text-white">{bill.provider_name}</p>
                                                                                        </div>
                                                                                </div>
                                                                        )}
                                                                        {bill.is_inpatient != null && (
                                                                                <div className="flex items-center gap-2.5">
                                                                                        <div className="p-1.5 bg-slate-500/10 rounded-lg border border-slate-500/20">
                                                                                                <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
                                                                                        </div>
                                                                                        <div>
                                                                                                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{t.info.visitType}</p>
                                                                                                <p className="text-sm font-semibold text-white">
                                                                                                        {bill.is_inpatient ? t.info.inpatient : t.info.outpatient}
                                                                                                </p>
                                                                                        </div>
                                                                                </div>
                                                                        )}
                                                                </motion.div>
                                                        )}

                                                        {/* ── Tabbed results ── */}
                                                        <motion.div
                                                                initial={{ opacity: 0, y: 16 }}
                                                                animate={{ opacity: 1, y: 0 }}
                                                                transition={{ delay: 0.25 }}
                                                                className="card overflow-hidden"
                                                        >
                                                                {/* Tab bar */}
                                                                <div className="flex border-b border-[#1e3a5f]/50">
                                                                        {TABS.map(({ id, label, Icon }) => (
                                                                                <button
                                                                                        key={id}
                                                                                        onClick={() => setTab(id)}
                                                                                        className={`flex-1 flex items-center justify-center gap-2
                                  px-4 py-4 text-sm font-semibold transition-all duration-200
                                  ${tab === id
                                                                                                        ? "text-blue-400 border-b-2 border-blue-500 bg-blue-500/5"
                                                                                                        : "text-slate-500 hover:text-slate-300 hover:bg-white/3"}`}
                                                                                >
                                                                                        <Icon className="w-4 h-4" />
                                                                                        <span className="hidden sm:inline">{label}</span>
                                                                                        {id === "issues" && result.issue_count > 0 && (
                                                                                                <span className="bg-blue-500/25 text-blue-300 text-[10px] font-bold
                                         px-1.5 py-0.5 rounded-full">{result.issue_count}</span>
                                                                                        )}
                                                                                </button>
                                                                        ))}
                                                                </div>

                                                                {/* Tab content */}
                                                                <div className="p-5 sm:p-6">
                                                                        <AnimatePresence mode="wait">
                                                                                {tab === "issues" && (
                                                                                        <motion.div key="i" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                                                                                <ResultsPanel auditResult={result} language={language} />
                                                                                        </motion.div>
                                                                                )}
                                                                                {tab === "pricing" && (
                                                                                        <motion.div key="p" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                                                                                <PricingSummary pricingResults={result.pricing_results} language={language} />
                                                                                        </motion.div>
                                                                                )}
                                                                                {tab === "appeal" && (
                                                                                        <motion.div key="a" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                                                                                <AppealDownload appealLetter={result.appeal_letter} language={language} />
                                                                                        </motion.div>
                                                                                )}
                                                                        </AnimatePresence>
                                                                </div>
                                                        </motion.div>

                                                </motion.div>
                                        )}
                                </AnimatePresence>
                        </main>

                        {/* ── AI Chatbot (only shown after audit results are ready) ── */}
                        {result && <Chatbot auditResult={result} language={language} />}
                </div>
        );
}
