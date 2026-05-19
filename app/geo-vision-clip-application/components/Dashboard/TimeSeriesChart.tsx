"use client";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { useAppStore } from "@/store/appStore";
import { getMockTimeSeries } from "@/lib/mockData";

interface TimeSeriesChartProps {
  contaminant: string;
  unit: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label, unit, isDark }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className={`px-3 py-2 rounded-lg text-xs font-mono border ${
      isDark ? "bg-slate-800 border-slate-700 text-slate-200" : "bg-white border-slate-200 text-slate-800"
    }`}>
      <div className="text-slate-500 mb-1">{label}</div>
      <div className="text-emerald-400 font-semibold">{payload[0].value.toFixed(1)} {unit}</div>
    </div>
  );
}

export function TimeSeriesChart({ contaminant, unit }: TimeSeriesChartProps) {
  const { theme } = useAppStore();
  const isDark = theme === "dark";
  const data = getMockTimeSeries(contaminant);

  const avg = data.reduce((acc, d) => acc + d.value, 0) / data.length;

  return (
    <div className={`rounded-xl p-3 ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}>
      <div className="flex items-center justify-between mb-3">
        <span className={`text-xs font-semibold ${isDark ? "text-slate-400" : "text-slate-600"}`}>
          Serie temporal (8 días)
        </span>
        <span className={`mono-value text-xs ${isDark ? "text-slate-500" : "text-slate-400"}`}>
          Prom: {avg.toFixed(1)} {unit}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={100}>
        <LineChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <XAxis
            dataKey="date"
            tick={{ fontSize: 9, fill: isDark ? "#64748b" : "#94a3b8", fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 9, fill: isDark ? "#64748b" : "#94a3b8", fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            content={<CustomTooltip unit={unit} isDark={isDark} />}
          />
          <ReferenceLine
            y={avg}
            stroke="#10b981"
            strokeDasharray="3 3"
            strokeOpacity={0.4}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ r: 2.5, fill: "#10b981", strokeWidth: 0 }}
            activeDot={{ r: 4, fill: "#10b981", stroke: "#0f172a", strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
