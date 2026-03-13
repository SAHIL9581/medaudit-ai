import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Loader2, Brain, Search, FileSearch, BarChart2, FileText, ShieldCheck } from "lucide-react";
import { getT } from "../services/translations";

const STAGE_ICONS = [FileSearch, Search, Brain, BarChart2, ShieldCheck, FileText];

const AnalysisProgress = ({ isActive, language = "en" }) => {
        const t = getT(language).progress;
        const STAGES = t.stages.map((label, i) => ({ icon: STAGE_ICONS[i], label, ms: [2800, 2400, 5200, 2000, 1600, 3200][i] }));

        const [current, setCurrent] = useState(0);
        const [done, setDone] = useState(new Set());

        useEffect(() => {
                if (!isActive) return;
                setCurrent(0);
                setDone(new Set());
                let elapsed = 0;
                const timers = STAGES.map((s, i) => {
                        const t = setTimeout(() => {
                                setCurrent(i);
                                setDone((prev) => { const n = new Set(prev); if (i > 0) n.add(i - 1); return n; });
                        }, elapsed);
                        elapsed += s.ms;
                        return t;
                });
                return () => timers.forEach(clearTimeout);
        }, [isActive]);

        if (!isActive) return null;

        const pct = Math.round((done.size / STAGES.length) * 100);

        return (
                <motion.div
                        initial={{ opacity: 0, scale: 0.97 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0 }}
                        className="max-w-xl mx-auto"
                >
                        <div className="card p-8">
                                {/* Animated icon */}
                                <div className="flex flex-col items-center mb-8">
                                        <div className="relative w-20 h-20 flex items-center justify-center mb-4">
                                                <motion.div
                                                        animate={{ rotate: 360 }}
                                                        transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                                                        className="absolute inset-0 rounded-full border-2 border-dashed border-blue-500/30"
                                                />
                                                <motion.div
                                                        animate={{ rotate: -360 }}
                                                        transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
                                                        className="absolute inset-2 rounded-full border border-blue-400/20"
                                                />
                                                <div className="p-4 bg-blue-500/15 rounded-2xl border border-blue-500/25">
                                                        <Brain className="w-8 h-8 text-blue-400" />
                                                </div>
                                        </div>
                                        <h2 className="text-xl font-bold text-white">{t.title}</h2>
                                        <p className="text-sm text-slate-500 mt-1">{t.subtitle}</p>
                                </div>

                                {/* Progress bar */}
                                <div className="mb-6">
                                        <div className="flex justify-between text-xs text-slate-500 mb-2">
                                                <span>{t.label}</span>
                                                <span className="font-mono text-blue-400">{pct}%</span>
                                        </div>
                                        <div className="h-1.5 bg-[#0a1628] rounded-full overflow-hidden">
                                                <motion.div
                                                        animate={{ width: `${pct}%` }}
                                                        transition={{ duration: 0.6, ease: "easeOut" }}
                                                        className="h-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400"
                                                />
                                        </div>
                                </div>

                                {/* Stage list */}
                                <div className="space-y-2">
                                        {STAGES.map((s, i) => {
                                                const Icon = s.icon;
                                                const isCompleted = done.has(i);
                                                const isRunning = current === i && !isCompleted;

                                                return (
                                                        <motion.div
                                                                key={i}
                                                                initial={{ opacity: 0, x: -8 }}
                                                                animate={{ opacity: 1, x: 0 }}
                                                                transition={{ delay: i * 0.06 }}
                                                                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300
                  ${isRunning ? "bg-blue-500/8 border border-blue-500/20" : ""}
                  ${isCompleted ? "opacity-60" : ""}
                  ${!isRunning && !isCompleted ? "opacity-40" : ""}
                `}
                                                        >
                                                                <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0
                  ${isCompleted ? "bg-emerald-500/20" : isRunning ? "bg-blue-500/20" : "bg-[#0a1628]"}`}>
                                                                        {isCompleted ? (
                                                                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                                                                        ) : isRunning ? (
                                                                                <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
                                                                                        <Loader2 className="w-3.5 h-3.5 text-blue-400" />
                                                                                </motion.div>
                                                                        ) : (
                                                                                <Icon className="w-3.5 h-3.5 text-slate-600" />
                                                                        )}
                                                                </div>

                                                                <span className={`text-sm font-medium
                  ${isCompleted ? "text-slate-400" : isRunning ? "text-blue-300" : "text-slate-600"}`}>
                                                                        {s.label}
                                                                </span>

                                                                {isRunning && (
                                                                        <div className="ml-auto flex gap-1 items-center">
                                                                                {[0, 1, 2].map((d) => (
                                                                                        <motion.div
                                                                                                key={d}
                                                                                                animate={{ opacity: [0.3, 1, 0.3] }}
                                                                                                transition={{ duration: 1.2, repeat: Infinity, delay: d * 0.2 }}
                                                                                                className="w-1 h-1 rounded-full bg-blue-400"
                                                                                        />
                                                                                ))}
                                                                        </div>
                                                                )}
                                                                {isCompleted && (
                                                                        <span className="ml-auto text-xs text-emerald-500 font-medium">Done</span>
                                                                )}
                                                        </motion.div>
                                                );
                                        })}
                                </div>
                        </div>
                </motion.div>
        );
};

export default AnalysisProgress;
