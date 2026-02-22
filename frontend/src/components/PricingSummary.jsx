import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, AlertCircle, CheckCircle } from "lucide-react";

const Bar = ({ pct, flagged }) => (
        <div className="flex items-center gap-2 w-full">
                <div className="flex-1 h-1.5 bg-[#0a1628] rounded-full overflow-hidden">
                        <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${Math.min(Math.abs(pct), 100)}%` }}
                                transition={{ duration: 0.7, ease: "easeOut" }}
                                className={`h-full rounded-full ${pct > 30 ? "bg-red-500" : pct > 10 ? "bg-amber-500" : "bg-emerald-500"
                                        }`}
                        />
                </div>
                <span className={`text-xs font-bold w-14 text-right tabular-nums
      ${pct > 30 ? "text-red-400" : pct > 10 ? "text-amber-400" : "text-emerald-400"}`}>
                        {pct > 0 ? "+" : ""}{pct.toFixed(1)}%
                </span>
        </div>
);

const PricingSummary = ({ pricingResults }) => {
        const flagged = pricingResults.filter((p) => p.is_flagged);
        const totalOver = pricingResults.reduce((s, p) => s + p.estimated_overcharge, 0);

        return (
                <div className="space-y-4">
                        {/* Summary banner */}
                        <div className={`card p-5 flex items-center gap-4
        ${totalOver > 0 ? "border-red-500/20 bg-red-500/5" : "border-emerald-500/20 bg-emerald-500/5"}`}>
                                <div className={`p-3 rounded-xl border
          ${totalOver > 0 ? "bg-red-500/15 border-red-500/25" : "bg-emerald-500/15 border-emerald-500/25"}`}>
                                        {totalOver > 0
                                                ? <AlertCircle className="w-6 h-6 text-red-400" />
                                                : <CheckCircle className="w-6 h-6 text-emerald-400" />}
                                </div>
                                <div className="flex-1">
                                        <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">
                                                Total Estimated Overcharge
                                        </p>
                                        <p className={`text-2xl font-extrabold mt-0.5
            ${totalOver > 0 ? "text-red-400" : "text-emerald-400"}`}>
                                                ${totalOver.toFixed(2)}
                                        </p>
                                </div>
                                <div className="text-right">
                                        <p className="text-2xl font-extrabold text-white">{flagged.length}</p>
                                        <p className="text-xs text-slate-500">of {pricingResults.length} flagged</p>
                                </div>
                        </div>

                        {/* Table */}
                        <div className="card overflow-hidden">
                                <div className="px-5 py-4 border-b border-[#1e3a5f]/50">
                                        <h3 className="text-sm font-bold text-white">CPT Code Pricing Breakdown</h3>
                                        <p className="text-xs text-slate-500 mt-0.5">vs. CMS Medicare benchmark median</p>
                                </div>
                                <div className="overflow-x-auto">
                                        <table className="w-full">
                                                <thead>
                                                        <tr className="border-b border-[#1e3a5f]/30">
                                                                {["CPT", "Description", "Billed", "Benchmark", "Deviation", "Overcharge"].map((h) => (
                                                                        <th key={h} className="text-left px-4 py-3 text-[11px] font-bold
                                         uppercase tracking-widest text-slate-600">{h}</th>
                                                                ))}
                                                        </tr>
                                                </thead>
                                                <tbody>
                                                        {pricingResults.map((r, i) => (
                                                                <motion.tr
                                                                        key={r.cpt_code}
                                                                        initial={{ opacity: 0 }}
                                                                        animate={{ opacity: 1 }}
                                                                        transition={{ delay: i * 0.03 }}
                                                                        className={`border-b border-[#1e3a5f]/20 hover:bg-white/2 transition-colors
                    ${r.is_flagged ? "bg-red-500/3" : ""}`}
                                                                >
                                                                        <td className="px-4 py-3">
                                                                                <span className={`font-mono text-xs font-bold px-2.5 py-1 rounded-lg
                      ${r.is_flagged
                                                                                                ? "bg-red-500/15 text-red-300 border border-red-500/20"
                                                                                                : "bg-[#0a1628] text-slate-300 border border-[#1e3a5f]/40"}`}>
                                                                                        {r.cpt_code}
                                                                                </span>
                                                                        </td>
                                                                        <td className="px-4 py-3 text-xs text-slate-500 max-w-[160px]">
                                                                                <span className="truncate block">{r.description || "—"}</span>
                                                                        </td>
                                                                        <td className="px-4 py-3 text-sm font-bold text-white tabular-nums">
                                                                                ${r.billed_amount.toFixed(2)}
                                                                        </td>
                                                                        <td className="px-4 py-3 text-sm text-slate-400 tabular-nums">
                                                                                {r.benchmark_median > 0 ? `$${r.benchmark_median.toFixed(2)}` : "—"}
                                                                        </td>
                                                                        <td className="px-4 py-3 w-44">
                                                                                {r.benchmark_median > 0
                                                                                        ? <Bar pct={r.deviation_percent} flagged={r.is_flagged} />
                                                                                        : <span className="text-xs text-slate-600">No data</span>}
                                                                        </td>
                                                                        <td className="px-4 py-3 text-sm tabular-nums">
                                                                                {r.estimated_overcharge > 0
                                                                                        ? <span className="font-bold text-red-400">${r.estimated_overcharge.toFixed(2)}</span>
                                                                                        : <span className="text-emerald-500 font-medium text-xs">Fair</span>}
                                                                        </td>
                                                                </motion.tr>
                                                        ))}
                                                </tbody>
                                        </table>
                                </div>
                        </div>
                </div>
        );
};

export default PricingSummary;
