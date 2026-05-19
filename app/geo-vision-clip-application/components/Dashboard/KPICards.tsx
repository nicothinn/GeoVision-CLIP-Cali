"use client";
import { useValidation } from "@/hooks/useValidation";
import { useAppStore } from "@/store/appStore";
import { Activity, BarChart3, Cpu, GitBranch } from "lucide-react";

interface KPIItemProps {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ReactNode;
  isDark: boolean;
}

function KPIItem({ label, value, sub, icon, isDark }: KPIItemProps) {
  return (
    <div className={`flex items-center gap-3 px-4 py-2.5 rounded-lg ${
      isDark ? "bg-slate-800" : "bg-white border border-slate-200"
    }`}>
      <div className="text-emerald-500">{icon}</div>
      <div>
        <div className={`text-xs ${isDark ? "text-slate-500" : "text-slate-400"}`}>{label}</div>
        <div className="mono-value text-sm font-bold text-emerald-400">{value}</div>
        {sub && <div className={`text-xs font-mono ${isDark ? "text-slate-600" : "text-slate-400"}`}>{sub}</div>}
      </div>
    </div>
  );
}

export function KPICards() {
  const { theme } = useAppStore();
  const { data } = useValidation();
  const isDark = theme === "dark";

  const kpis = data?.kpis;
  const moran = data?.moran_i;

  return (
    <div
      className={`rounded-2xl px-5 py-4 border ${
        isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200"
      }`}
    >
      <div className="flex items-center gap-2 mb-3">
        <span className={`text-xs font-semibold uppercase tracking-wider ${isDark ? "text-slate-500" : "text-slate-400"}`}>
          KPIs del modelo
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
        <KPIItem
          label="Recall@1"
          value={kpis ? (kpis.recall_at_1 * 100).toFixed(0) + "%" : "—"}
          icon={<Activity className="w-4 h-4" />}
          isDark={isDark}
        />
        <KPIItem
          label="Recall@5"
          value={kpis ? (kpis.recall_at_5 * 100).toFixed(0) + "%" : "—"}
          icon={<BarChart3 className="w-4 h-4" />}
          isDark={isDark}
        />
        <KPIItem
          label="Sparsity SAE"
          value={kpis ? kpis.sparsity_sae.toFixed(2) : "—"}
          icon={<Cpu className="w-4 h-4" />}
          isDark={isDark}
        />
        <KPIItem
          label="Moran I"
          value={moran ? moran.I.toFixed(2) : "—"}
          sub={moran ? `p=${moran.p_value}` : undefined}
          icon={<GitBranch className="w-4 h-4" />}
          isDark={isDark}
        />
        <KPIItem
          label="SAE Recon Loss"
          value={kpis ? kpis.loss_sae_recon.toFixed(3) : "—"}
          icon={<Activity className="w-4 h-4" />}
          isDark={isDark}
        />
      </div>
    </div>
  );
}
