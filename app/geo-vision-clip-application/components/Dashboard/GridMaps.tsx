"use client";
import dynamic from "next/dynamic";
import { useAppStore } from "@/store/appStore";
import { CONTAMINANTS, HORIZONS } from "@/lib/constants";
import { CALI_CENTER } from "@/lib/constants";

const MiniMapInner = dynamic(() => import("@/components/Map/MiniMapInner"), {
  ssr: false,
  loading: () => <div className="h-32 w-full rounded-lg bg-slate-800 animate-pulse" />,
});

export function GridMaps() {
  const { theme, selectedPoint } = useAppStore();
  const isDark = theme === "dark";

  const lat = selectedPoint?.lat ?? CALI_CENTER[0];
  const lon = selectedPoint?.lon ?? CALI_CENTER[1];

  // Helper to format contaminant name with subscript
  const formatContaminant = (c: string) => {
    if (c === "NO2") return "NO₂";
    if (c === "SO2") return "SO₂";
    if (c === "O3") return "O₃";
    return c;
  };

  return (
    <div className="w-full">
      {/* Header row: empty corner + 3 horizon labels */}
      <div className="grid grid-cols-[80px_1fr_1fr_1fr] gap-3 mb-2 px-1">
        <div /> {/* empty corner cell */}
        {HORIZONS.map((hz) => (
          <div key={hz} className="flex items-center justify-center">
            <span
              className={`text-xs font-mono font-semibold px-3 py-1 rounded-full ${
                isDark
                  ? "bg-slate-800 text-emerald-400"
                  : "bg-slate-200 text-emerald-600"
              }`}
            >
              {hz}
            </span>
          </div>
        ))}
      </div>

      {/* Rows: contaminant label + 3 maps */}
      {CONTAMINANTS.map((cont) => (
        <div
          key={cont}
          className="grid grid-cols-[80px_1fr_1fr_1fr] gap-3 mb-3 items-center"
        >
          {/* Row label (mismo estilo que columnas) */}
          <div className="flex items-center justify-center">
            <span
              className={`text-xs font-mono font-semibold px-3 py-1 rounded-full ${
                isDark ? "bg-slate-800 text-emerald-400" : "bg-slate-200 text-emerald-600"
              }`}
            >
              {formatContaminant(cont)}
            </span>
          </div>

          {/* 3 horizon maps */}
          {HORIZONS.map((hz) => (
            <MiniMapInner
              key={`${cont}-${hz}`}
              contaminant={cont}
              horizon={hz}
              theme={theme}
            />
          ))}
        </div>
      ))}

      {/* Bottom label */}
      <div className="flex justify-end mt-1">
        <span
          className={`text-xs font-mono ${
            isDark ? "text-slate-600" : "text-slate-400"
          }`}
        >
          {selectedPoint
            ? `${lat.toFixed(4)}, ${lon.toFixed(4)}`
            : "Centro de Cali"}
        </span>
      </div>
    </div>
  );
}
