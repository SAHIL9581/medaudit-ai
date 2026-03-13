import React from "react";
import { Globe } from "lucide-react";

const LANGUAGES = [
    { code: "en", label: "English" },
    { code: "hi", label: "हिंदी" },
    { code: "ta", label: "தமிழ்" },
    { code: "es", label: "Español" },
];

export default function LanguageSelector({ language, onChange }) {
    return (
        <div className="flex items-center gap-2">
            <div className="p-1.5 bg-slate-700/40 rounded-lg border border-slate-600/30">
                <Globe className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <select
                value={language}
                onChange={(e) => onChange(e.target.value)}
                className="bg-[#0a1628] border border-[#1e3a5f]/60 text-slate-300
                           text-sm rounded-lg px-2.5 py-1.5 outline-none
                           focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30
                           transition-colors cursor-pointer"
                aria-label="Select language"
            >
                {LANGUAGES.map(({ code, label }) => (
                    <option key={code} value={code}>
                        {label}
                    </option>
                ))}
            </select>
        </div>
    );
}
