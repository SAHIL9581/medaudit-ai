import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, CheckCircle, XCircle, ChevronDown, Info, Shield, Target, TrendingUp } from "lucide-react";
import { getT } from "../services/translations";


function normalizeIssueTypeKey(issueType) {
  const u = (issueType || '').toUpperCase();
  if (u.includes('UPCODE') || u.includes('UPCODING')) return 'UPCODING';
  if (u.includes('DUPLICATE')) return 'DUPLICATE_BILLING';
  if (u.includes('NCCI') || u.includes('UNBUNDL')) return 'UNBUNDLING';
  if (u.includes('CPT') && u.includes('ANOMALY')) return 'CPT_ANOMALY';
  if (u.includes('INPATIENT') && (u.includes('MISMATCH') || u.includes('CODE'))) return 'INPATIENT_MISMATCH';
  if (u.includes('MODIFIER')) return 'MODIFIER_ABUSE';
  if (u.includes('CODING') && u.includes('ERROR')) return 'CODING_ERROR';
  if (u.includes('MEDICAL') || u.includes('NECESSITY')) return 'MEDICAL_NECESSITY';
  if (u.includes('PRICING') || u.includes('ANOMALY')) return 'PRICING_ANOMALY';
  return u.replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}

const riskMap = {
        high: { cls: "risk-high", Icon: XCircle, border: "border-red-500/15", bg: "bg-red-500/5" },
        medium: { cls: "risk-medium", Icon: AlertTriangle, border: "border-amber-500/15", bg: "bg-amber-500/5" },
        low: { cls: "risk-low", Icon: CheckCircle, border: "border-emerald-500/15", bg: "bg-emerald-500/5" },
};


const IssueCard = ({ issue, index, t }) => {
        const [open, setOpen] = useState(false);
        const { cls, Icon, border, bg } = riskMap[issue.risk_level] || riskMap.medium;
        const friendlyType = t.issueTypes[normalizeIssueTypeKey(issue.issue_type)] || issue.issue_type;
        const riskLabel = issue.risk_level === "high" ? t.riskHigh : issue.risk_level === "medium" ? t.riskMedium : t.riskLow;


        return (
                <motion.div
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.04 }}
                        className={`border rounded-xl overflow-hidden ${border} ${bg}`}
                >
                        <button
                                onClick={() => setOpen(!open)}
                                className="w-full flex items-center gap-3 p-4 text-left hover:bg-white/3 transition-colors"
                        >
                                <Icon className={`w-5 h-5 flex-shrink-0 ${cls.replace('risk-', 'text-').replace('high', 'red-400').replace('medium', 'amber-400').replace('low', 'emerald-400')}`} />


                                <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap gap-y-1">
                                                <span className="text-sm font-semibold text-white">{friendlyType}</span>
                                                {issue.cpt_code && (
                                                        <span className="text-[11px] bg-[#0a1628] border border-[#1e3a5f]/60 text-slate-300
                               px-2 py-0.5 rounded-md font-mono">{t.codeLabel}: {issue.cpt_code}</span>
                                                )}
                                                <span className={cls}>{riskLabel}</span>
                                        </div>
                                        <p className="text-xs text-slate-500 mt-1 line-clamp-1">{issue.description}</p>
                                </div>


                                <div className="flex items-center gap-3 flex-shrink-0 ml-2">
                                        <div className="text-right hidden sm:block">
                                                <div className="text-[10px] text-slate-600 uppercase tracking-wide">{t.sureLabel}</div>
                                                <div className="text-sm font-bold text-white">{(issue.confidence * 100).toFixed(0)}%</div>
                                        </div>
                                        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
                                                <ChevronDown className="w-4 h-4 text-slate-500" />
                                        </motion.div>
                                </div>
                        </button>


                        <AnimatePresence>
                                {open && (
                                        <motion.div
                                                initial={{ height: 0, opacity: 0 }}
                                                animate={{ height: "auto", opacity: 1 }}
                                                exit={{ height: 0, opacity: 0 }}
                                                transition={{ duration: 0.2 }}
                                                className="overflow-hidden"
                                        >
                                                <div className="px-4 pb-4 space-y-3 border-t border-white/5 pt-3">
                                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                                                <div className="bg-[#060d1a]/60 rounded-xl p-3 border border-[#1e3a5f]/30">
                                                                        <p className="section-label flex items-center gap-1">
                                                                                <Shield className="w-3 h-3" /> {t.whyFlagged}
                                                                        </p>
                                                                        <p className="text-xs text-slate-300 leading-relaxed">{issue.rule_triggered}</p>
                                                                </div>
                                                                <div className="bg-[#060d1a]/60 rounded-xl p-3 border border-[#1e3a5f]/30">
                                                                        <p className="section-label flex items-center gap-1">
                                                                                <Target className="w-3 h-3" /> {t.whatToDo}
                                                                        </p>
                                                                        <p className="text-xs text-slate-300 leading-relaxed">{issue.suggested_action}</p>
                                                                </div>
                                                        </div>


                                                        {issue.estimated_overcharge > 0 && (
                                                                <div className="flex items-center gap-2 bg-red-500/8 border border-red-500/20 rounded-xl p-3">
                                                                        <TrendingUp className="w-4 h-4 text-red-400 flex-shrink-0" />
                                                                        <p className="text-sm text-red-300">
                                                                                {t.overchargedBy} <span className="font-bold">${issue.estimated_overcharge.toFixed(2)}</span>
                                                                        </p>
                                                                </div>
                                                        )}


                                                        {issue.cpt_reference && (
                                                                <div className="flex items-start gap-2 bg-blue-500/8 border border-blue-500/20 rounded-xl p-3">
                                                                        <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                                                                        <p className="text-xs text-blue-300 leading-relaxed">{issue.cpt_reference}</p>
                                                                </div>
                                                        )}
                                                </div>
                                        </motion.div>
                                )}
                        </AnimatePresence>
                </motion.div>
        );
};


const ResultsPanel = ({ auditResult, language = "en" }) => {
        const t = getT(language).results;
        const tInfo = getT(language).info;
        const { issues, extracted_bill } = auditResult;
        const high = issues.filter((i) => i.risk_level === "high");
        const med = issues.filter((i) => i.risk_level === "medium");
        const low = issues.filter((i) => i.risk_level === "low");


        return (
                <div className="space-y-4">
                        {/* Risk counts */}
                        <div className="grid grid-cols-3 gap-3">
                                {[
                                        { label: t.serious, count: high.length, cls: "border-red-500/20 bg-red-500/5 text-red-400" },
                                        { label: t.possible, count: med.length, cls: "border-amber-500/20 bg-amber-500/5 text-amber-400" },
                                        { label: t.minor, count: low.length, cls: "border-emerald-500/20 bg-emerald-500/5 text-emerald-400" },
                                ].map(({ label, count, cls }) => (
                                        <div key={label} className={`border rounded-xl p-4 text-center ${cls}`}>
                                                <div className="text-3xl font-extrabold">{count}</div>
                                                <div className="text-xs mt-1 opacity-70 font-medium">{label}</div>
                                        </div>
                                ))}
                        </div>


                        {/* Bill metadata */}
                        {(extracted_bill.provider_name || extracted_bill.patient_name) && (
                                <div className="card px-4 py-3 flex flex-wrap gap-4 text-sm">
                                        {extracted_bill.provider_name && (
                                                <div><span className="text-slate-500">{tInfo.provider} </span>
                                                        <span className="text-white font-semibold">{extracted_bill.provider_name}</span></div>
                                        )}
                                        {extracted_bill.patient_name && (
                                                <div><span className="text-slate-500">{tInfo.patient} </span>
                                                        <span className="text-white font-semibold">{extracted_bill.patient_name}</span></div>
                                        )}
                                        {extracted_bill.is_inpatient != null && (
                                                <div><span className="text-slate-500">{tInfo.visitType} </span>
                                                        <span className="text-white font-semibold">
                                                                {extracted_bill.is_inpatient ? tInfo.inpatient : tInfo.outpatient}
                                                        </span></div>
                                        )}
                                </div>
                        )}


                        {/* Issues */}
                        {issues.length === 0 ? (
                                <div className="card p-10 flex flex-col items-center text-center">
                                        <div className="p-4 bg-emerald-500/15 rounded-2xl border border-emerald-500/25 mb-4">
                                                <CheckCircle className="w-10 h-10 text-emerald-400" />
                                        </div>
                                        <h3 className="text-lg font-bold text-white">{t.allClearTitle}</h3>
                                        <p className="text-slate-500 text-sm mt-1 max-w-xs">
                                                {t.allClearSub}
                                        </p>
                                </div>
                        ) : (
                                <div className="space-y-2">
                                        {[...high, ...med, ...low].map((issue, i) => (
                                                <IssueCard key={i} issue={issue} index={i} t={t} />
                                        ))}
                                </div>
                        )}
                </div>
        );
};


export default ResultsPanel;
