import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, Upload, X, CheckCircle, Sparkles } from "lucide-react";
import { getT } from "../services/translations";

const DropZone = ({ label, hint, badge, isRequired, dropText, releaseText, file, onDrop, onRemove }) => {
        const { getRootProps, getInputProps, isDragActive } = useDropzone({
                onDrop: (f) => f[0] && onDrop(f[0]),
                accept: { "application/pdf": [".pdf"] },
                maxFiles: 1,
                maxSize: 20 * 1024 * 1024,
        });

        return (
                <div className="space-y-2">
                        {/* Label row */}
                        <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-slate-200">{label}</span>
                                <span className={isRequired ? "badge-required" : "badge-optional"}>
                                        {badge}
                                </span>
                        </div>

                        <AnimatePresence mode="wait">
                                {file ? (
                                        <motion.div
                                                key="filled"
                                                initial={{ opacity: 0, y: 4 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: -4 }}
                                                className="flex items-center gap-3 px-4 py-3
                       bg-emerald-500/8 border border-emerald-500/30 rounded-xl"
                                        >
                                                <div className="p-1.5 bg-emerald-500/20 rounded-lg">
                                                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-medium text-emerald-300 truncate">{file.name}</p>
                                                        <p className="text-xs text-slate-500 mt-0.5">{(file.size / 1024).toFixed(0)} KB · PDF</p>
                                                </div>
                                                <button
                                                        onClick={(e) => { e.stopPropagation(); onRemove(); }}
                                                        className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-slate-500 hover:text-slate-300"
                                                >
                                                        <X className="w-3.5 h-3.5" />
                                                </button>
                                        </motion.div>
                                ) : (
                                        <motion.div
                                                key="empty"
                                                initial={{ opacity: 0, y: 4 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: -4 }}
                                                {...getRootProps()}
                                                className={`relative flex items-center gap-4 px-5 py-4 rounded-xl cursor-pointer
                        border-2 border-dashed transition-all duration-200
                        ${isDragActive
                                                                ? "border-blue-400 bg-blue-500/8 scale-[1.01]"
                                                                : "border-[#1e3a5f] hover:border-blue-500/50 hover:bg-[#0f2440]"
                                                        }`}
                                        >
                                                <input {...getInputProps()} />
                                                <div className={`p-2.5 rounded-xl transition-colors
              ${isDragActive ? "bg-blue-500/20" : "bg-[#0a1628]"}`}>
                                                        <Upload className={`w-5 h-5 ${isDragActive ? "text-blue-400" : "text-slate-500"}`} />
                                                </div>
                                                <div>
                                                        <p className={`text-sm font-medium transition-colors
                ${isDragActive ? "text-blue-300" : "text-slate-400"}`}>
                                                                {isDragActive ? releaseText : dropText}
                                                        </p>
                                                        <p className="text-xs text-slate-600 mt-0.5">{hint}</p>
                                                </div>
                                        </motion.div>
                                )}
                        </AnimatePresence>
                </div>
        );
};

const UploadSection = ({ onSubmit, isLoading, language = "en" }) => {
        const t = getT(language).upload;
        const [files, setFiles] = useState({ bill: null, summary: null, eob: null });

        const set = (k) => (v) => setFiles((p) => ({ ...p, [k]: v }));
        const clear = (k) => () => setFiles((p) => ({ ...p, [k]: null }));
        const ready = !!files.bill && !isLoading;

        return (
                <motion.div
                        initial={{ opacity: 0, y: 24 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4 }}
                        className="max-w-xl mx-auto"
                >
                        <div className="card p-7 space-y-5">

                                {/* Card header */}
                                <div className="flex items-center gap-3 pb-4 border-b border-[#1e3a5f]/50">
                                        <div className="p-2.5 bg-blue-500/15 rounded-xl border border-blue-500/20">
                                                <FileText className="w-5 h-5 text-blue-400" />
                                        </div>
                                        <div>
                                                <h2 className="text-base font-bold text-white">{t.title}</h2>
                                                <p className="text-xs text-slate-500 mt-0.5">{t.subtitle}</p>
                                        </div>
                                </div>

                                {/* Drop zones */}
                                <DropZone
                                        label={t.billLabel}
                                        hint={t.billHint}
                                        badge={t.required}
                                        isRequired={true}
                                        dropText={t.dropHere}
                                        releaseText={t.release}
                                        file={files.bill}
                                        onDrop={set("bill")}
                                        onRemove={clear("bill")}
                                />
                                <DropZone
                                        label={t.summaryLabel}
                                        hint={t.summaryHint}
                                        badge={t.optional}
                                        isRequired={false}
                                        dropText={t.dropHere}
                                        releaseText={t.release}
                                        file={files.summary}
                                        onDrop={set("summary")}
                                        onRemove={clear("summary")}
                                />
                                <DropZone
                                        label={t.eobLabel}
                                        hint={t.eobHint}
                                        badge={t.optional}
                                        isRequired={false}
                                        dropText={t.dropHere}
                                        releaseText={t.release}
                                        file={files.eob}
                                        onDrop={set("eob")}
                                        onRemove={clear("eob")}
                                />

                                {/* CTA */}
                                <motion.button
                                        onClick={() => ready && onSubmit(files)}
                                        disabled={!ready}
                                        whileHover={ready ? { scale: 1.015 } : {}}
                                        whileTap={ready ? { scale: 0.985 } : {}}
                                        className="btn-primary w-full flex items-center justify-center gap-2 mt-2"
                                >
                                        <Sparkles className="w-4 h-4" />
                                        {isLoading ? t.checking : t.cta}
                                </motion.button>

                                <p className="text-center text-xs text-slate-600">
                                        {t.privacy}
                                </p>
                        </div>
                </motion.div>
        );
};

export default UploadSection;
