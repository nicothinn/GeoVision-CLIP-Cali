"use client";
import dynamic from "next/dynamic";
import { useAppStore } from "@/store/appStore";
import { CONTAMINANTS, HORIZONS } from "@/lib/constants";
import { getMockPrediction } from "@/lib/mockData";
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

  return (
    <div className="w-full">
      {/* Column headers */}
      <div className={`grid grid-cols-3 gap-3 mb-2 px-1`}>
        {HORIZONS.map((hz) => (
          <div key={hz} className="flex items-center justify-center">
            <span className={`text-xs font-mono font-semibold px-3 py-1 rounded-full ${
              isDark ? "bg-slate-800 text-emerald-400" : "bg-slate-200 text-emerald-600"
            }`}>
              {hz}
            </span>
          </div>
        ))}
      </div>
      {/* Rows per contaminant */}
      {CONTAMINANTS.map((cont) => (
        <div key={cont} className="grid grid-cols-3 gap-3 mb-3 items-center">
          {HORIZONS.map((hz) => {
            const pred = getMockPrediction(lat, lon, 5, cont, hz);
            return (
              <MiniMapInner
                key={`${cont}-${hz}`}
                contaminant={cont}
                horizon={hz}
                data={pred.grid}
                theme={theme}
              />
            );
          })}
        </div>
      ))}
      {/* Bottom label */}
      <div className="flex justify-end mt-1">
        <span className={`text-xs font-mono ${isDark ? "text-slate-600" : "text-slate-400"}`}>
          {selectedPoint ? `${lat.toFixed(4)}, ${lon.toFixed(4)}` : "Centro de Cali"}
        </span>
      </div>
    </div>
  );
}
