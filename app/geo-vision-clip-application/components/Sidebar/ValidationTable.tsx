"use client";
import { useValidation } from "@/hooks/useValidation";
import { useAppStore } from "@/store/appStore";

export function ValidationTable() {
  const { theme } = useAppStore();
  const { data, isLoading } = useValidation();
  const isDark = theme === "dark";

  const loo = data?.loo_cv;

  return (
    <div className={`rounded-xl overflow-hidden ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}>
      <div className={`px-3 py-2 border-b ${isDark ? "border-slate-700" : "border-slate-100"}`}>
        <span className={`text-xs font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>
          Validación LOO-CV
        </span>
      </div>
      <table className="w-full text-xs">
        <thead>
          <tr className={isDark ? "bg-slate-700/50" : "bg-slate-50"}>
            <th className={`text-left px-3 py-1.5 font-mono font-semibold ${isDark ? "text-slate-400" : "text-slate-500"}`}>Gas</th>
            <th className={`text-right px-2 py-1.5 font-mono font-semibold ${isDark ? "text-slate-400" : "text-slate-500"}`}>RMSE</th>
            <th className={`text-right px-2 py-1.5 font-mono font-semibold ${isDark ? "text-slate-400" : "text-slate-500"}`}>MAE</th>
            <th className={`text-right px-3 py-1.5 font-mono font-semibold ${isDark ? "text-slate-400" : "text-slate-500"}`}>R²</th>
          </tr>
        </thead>
        <tbody className={`divide-y ${isDark ? "divide-slate-700/50" : "divide-slate-100"}`}>
          {isLoading
            ? [1, 2, 3].map((i) => (
                <tr key={i}>
                  {[1, 2, 3, 4].map((j) => (
                    <td key={j} className="px-3 py-2">
                      <div className={`h-3 rounded animate-pulse ${isDark ? "bg-slate-700" : "bg-slate-200"}`} />
                    </td>
                  ))}
                </tr>
              ))
            : (["NO2", "SO2", "O3"] as const).map((c) => {
                const metrics = loo?.[c];
                return (
                  <tr key={c} className={isDark ? "hover:bg-slate-700/30" : "hover:bg-slate-50"}>
                    <td className="px-3 py-2">
                      <span className="mono-value font-semibold text-emerald-400">
                        {c === "NO2" ? "NO₂" : c === "SO2" ? "SO₂" : "O₃"}
                      </span>
                    </td>
                    <td className={`px-2 py-2 text-right mono-value ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                      {metrics?.RMSE.toFixed(1) ?? "—"}
                    </td>
                    <td className={`px-2 py-2 text-right mono-value ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                      {metrics?.MAE.toFixed(1) ?? "—"}
                    </td>
                    <td className={`px-3 py-2 text-right mono-value font-semibold ${
                      metrics && metrics.R2 > 0.65 ? "text-emerald-400" : "text-amber-400"
                    }`}>
                      {metrics?.R2.toFixed(2) ?? "—"}
                    </td>
                  </tr>
                );
              })}
        </tbody>
      </table>
    </div>
  );
}
