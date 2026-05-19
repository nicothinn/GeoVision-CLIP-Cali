"use client";
import { Radio, Layers, MapPin } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { DAGMA_STATIONS, CONTAMINANT_META } from "@/lib/constants";
import { useStations } from "@/hooks/useStations";

export function Sidebar() {
  const { theme, contaminant, radiusKm, setRadius, selectedPoint } = useAppStore();
  const { data: stationsData } = useStations();
  const isDark = theme === "dark";

  const stations = stationsData?.stations ?? DAGMA_STATIONS.map((s) => ({ ...s, last_reading: undefined }));

  return (
    <aside
      className={`flex flex-col gap-4 p-4 overflow-y-auto ${
        isDark ? "bg-slate-900" : "bg-slate-50"
      } w-64 shrink-0`}
    >
      {/* Selected point */}
      {selectedPoint && (
        <div className={`rounded-xl p-3 ${isDark ? "bg-emerald-500/10 border border-emerald-500/30" : "bg-emerald-50 border border-emerald-200"}`}>
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="w-3.5 h-3.5 text-emerald-500" />
            <span className={`text-xs font-semibold ${isDark ? "text-emerald-400" : "text-emerald-700"}`}>
              Punto seleccionado
            </span>
          </div>
          <div className="font-mono text-xs space-y-0.5">
            <div className={isDark ? "text-slate-300" : "text-slate-700"}>
              Lat: {selectedPoint.lat.toFixed(4)}
            </div>
            <div className={isDark ? "text-slate-300" : "text-slate-700"}>
              Lon: {selectedPoint.lon.toFixed(4)}
            </div>
          </div>
        </div>
      )}

      {/* Radius Control */}
      <div className={`rounded-xl p-3 ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}>
        <div className="flex items-center gap-2 mb-3">
          <Radio className="w-3.5 h-3.5 text-emerald-500" />
          <span className={`text-xs font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>
            Radio de análisis
          </span>
        </div>
        <div className="flex items-center justify-between mb-2">
          <span className={`text-xs ${isDark ? "text-slate-500" : "text-slate-400"}`}>1 km</span>
          <span className="mono-value text-emerald-500 text-sm font-semibold">{radiusKm} km</span>
          <span className={`text-xs ${isDark ? "text-slate-500" : "text-slate-400"}`}>15 km</span>
        </div>
        <input
          type="range"
          min={1}
          max={15}
          step={1}
          value={radiusKm}
          onChange={(e) => setRadius(parseInt(e.target.value))}
          className="w-full h-1.5 rounded-full cursor-pointer"
          aria-label="Radio de análisis en kilómetros"
        />
      </div>

      {/* Contaminant info */}
      <div className={`rounded-xl p-3 ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}>
        <div className="flex items-center gap-2 mb-2">
          <Layers className="w-3.5 h-3.5 text-emerald-500" />
          <span className={`text-xs font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>
            Contaminante activo
          </span>
        </div>
        <div>
          <div className={`text-base font-semibold ${isDark ? "text-slate-100" : "text-slate-900"}`}>
            {contaminant === "NO2" ? "NO₂" : contaminant === "SO2" ? "SO₂" : "O₃"}
          </div>
          <div className={`text-xs mt-0.5 ${isDark ? "text-slate-400" : "text-slate-500"}`}>
            {CONTAMINANT_META[contaminant]?.label}
          </div>
          <div className={`text-xs font-mono mt-1 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
            Unidad: {CONTAMINANT_META[contaminant]?.unit}
          </div>
        </div>
      </div>

      {/* Station list */}
      <div className={`rounded-xl overflow-hidden ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}>
        <div className={`px-3 py-2 border-b ${isDark ? "border-slate-700" : "border-slate-100"}`}>
          <span className={`text-xs font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>
            Estaciones DAGMA
          </span>
        </div>
        <div className="divide-y divide-slate-700/50">
          {stations.slice(0, 9).map((station) => {
            const reading = (station as { last_reading?: Record<string, number> }).last_reading?.[contaminant];
            return (
              <div key={station.id} className="px-3 py-2 flex items-center justify-between">
                <div>
                  <div className={`text-xs font-medium truncate max-w-[110px] ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                    {station.name.replace("Estación ", "")}
                  </div>
                  <div className={`text-xs ${isDark ? "text-slate-600" : "text-slate-400"}`}>
                    {station.zone}
                  </div>
                </div>
                <div className="text-right">
                  {reading !== undefined ? (
                    <span className="mono-value text-xs text-emerald-400 font-semibold">
                      {reading.toFixed(1)}
                    </span>
                  ) : (
                    <span className={`text-xs ${isDark ? "text-slate-600" : "text-slate-400"}`}>—</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
