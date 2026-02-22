import React, { useState } from "react";
import { motion } from "framer-motion";
import { Download, Copy, CheckCheck, FileText, Edit3, Eye } from "lucide-react";
import { downloadAppealPDF } from "../services/api";

const AppealDownload = ({ appealLetter }) => {
        const [copied, setCopied] = useState(false);
        const [downloading, setDownloading] = useState(false);
        const [editMode, setEditMode] = useState(false);
        const [text, setText] = useState(appealLetter.letter_text);

        const handleCopy = () => {
                navigator.clipboard.writeText(text);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
        };

        const handleDownload = async () => {
                setDownloading(true);
                try {
                        await downloadAppealPDF({ ...appealLetter, letter_text: text });
                } catch (e) {
                        alert("PDF download failed: " + e.message);
                } finally {
                        setDownloading(false);
                }
        };

        return (
                <div className="space-y-4">
                        {/* Header card */}
                        <div className="card p-5">
                                <div className="flex items-start justify-between gap-4 flex-wrap">
                                        <div className="flex items-center gap-3">
                                                <div className="p-2.5 bg-blue-500/15 rounded-xl border border-blue-500/20">
                                                        <FileText className="w-5 h-5 text-blue-400" />
                                                </div>
                                                <div>
                                                        <h3 className="text-sm font-bold text-white">Appeal Letter Ready</h3>
                                                        <p className="text-xs text-slate-500 mt-0.5">
                                                                Estimated overcharge: <span className="text-red-400 font-semibold">
                                                                        ${appealLetter.total_estimated_overcharge.toFixed(2)}</span>
                                                                {appealLetter.cpt_references.length > 0 &&
                                                                        <> · CPT: <span className="text-slate-400 font-mono text-[11px]">
                                                                                {appealLetter.cpt_references.join(", ")}</span></>}
                                                        </p>
                                                </div>
                                        </div>

                                        <div className="flex items-center gap-2 flex-wrap">
                                                <button
                                                        onClick={() => setEditMode(!editMode)}
                                                        className="btn-ghost flex items-center gap-1.5 text-xs"
                                                >
                                                        {editMode ? <Eye className="w-3.5 h-3.5" /> : <Edit3 className="w-3.5 h-3.5" />}
                                                        {editMode ? "Preview" : "Edit"}
                                                </button>
                                                <button
                                                        onClick={handleCopy}
                                                        className="btn-ghost flex items-center gap-1.5 text-xs"
                                                >
                                                        {copied
                                                                ? <><CheckCheck className="w-3.5 h-3.5 text-emerald-400" /> Copied</>
                                                                : <><Copy className="w-3.5 h-3.5" /> Copy</>}
                                                </button>
                                                <button
                                                        onClick={handleDownload}
                                                        disabled={downloading}
                                                        className="btn-primary flex items-center gap-1.5 text-sm px-4 py-2"
                                                >
                                                        <Download className="w-4 h-4" />
                                                        {downloading ? "Generating…" : "Download PDF"}
                                                </button>
                                        </div>
                                </div>
                        </div>

                        {/* Issues cited */}
                        {appealLetter.issues_summary.length > 0 && (
                                <div className="card p-5">
                                        <p className="section-label">Issues cited in this letter</p>
                                        <ul className="space-y-2">
                                                {appealLetter.issues_summary.map((issue, i) => (
                                                        <li key={i} className="flex items-start gap-2.5 text-xs text-slate-400">
                                                                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0 mt-1.5" />
                                                                {issue}
                                                        </li>
                                                ))}
                                        </ul>
                                </div>
                        )}

                        {/* Letter body */}
                        <div className="card p-5">
                                <p className="section-label">Letter Content</p>
                                {editMode ? (
                                        <textarea
                                                value={text}
                                                onChange={(e) => setText(e.target.value)}
                                                className="input-like w-full h-96 p-4 text-sm font-mono text-slate-300
                       leading-relaxed resize-y"
                                        />
                                ) : (
                                        <div className="bg-[#060d1a] border border-[#1e3a5f]/40 rounded-xl p-5
                          max-h-[480px] overflow-y-auto">
                                                <pre className="text-sm text-slate-300 whitespace-pre-wrap leading-7 font-sans">
                                                        {text}
                                                </pre>
                                        </div>
                                )}
                        </div>
                </div>
        );
};

export default AppealDownload;
