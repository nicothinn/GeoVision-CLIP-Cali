"use client";
import { Loader2, MousePointer, TrendingUp, AlertCircle } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { usePrediction } from "@/hooks/usePrediction";
import { CONTAMINANT_META } from "@/lib/constants";
import { TimeSeriesChart } from "./TimeSeriesChart";
import { DownloadButtons } from "./DownloadButtons";

export function PredictionPanel() {
  const { theme, selectedPoint, contaminant, horizon, radiusKm } = useAppStore();
  const isDark = theme === "dark";

  const { data, isLoading, isError } = usePrediction({
    lat: selectedPoint?.lat ?? null,
    lon: selectedPoint?.lon ?? null,
    radiusKm,
    contaminant,
    horizon,
  });

  const meta = CONTAMINANT_META[contaminant];

  return (
    <aside
      className={`flex flex-col gap-4 p-4 overflow-y-auto ${
        isDark ? "bg-slate-900" : "bg-slate-50"
      }`}
    >
      {/* Header */}
      <div>
        <h2 className={`text-xs font-semibold uppercase tracking-wider mb-1 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
          Panel de predicción
        </h2>
        <div className={`text-xs ${isDark ? "text-slate-600" : "text-slate-400"}`}>
          Haz clic en el mapa para predecir
        </div>
      </div>

      {/* No point selected */}
      {!selectedPoint && (
        <div className={`flex flex-col items-center justify-center gap-3 py-8 rounded-xl ${
          isDark ? "bg-slate-800" : "bg-white border border-slate-200"
        }`}>
          <MousePointer className={`w-8 h-8 ${isDark ? "text-slate-600" : "text-slate-300"}`} />
          <p className={`text-xs text-center px-4 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
            Selecciona un punto en el mapa para ver la predicción de contaminantes
          </p>
        </div>
      )}

      {/* Loading */}
      {selectedPoint && isLoading && (
        <div className={`flex flex-col items-center justify-center gap-3 py-8 rounded-xl ${
          isDark ? "bg-slate-800" : "bg-white border border-slate-200"
        }`}>
          <Loader2 className="w-6 h-6 text-emerald-500 animate-spin" />
          <span className={`text-xs ${isDark ? "text-slate-400" : "text-slate-500"}`}>
            Ejecutando modelo GeoVision-CLIP...
          </span>
        </div>
      )}

      {/* Error */}
      {selectedPoint && isError && (
        <div className={`flex flex-col items-center gap-2 p-4 rounded-xl ${
          isDark ? "bg-rose-900/20 border border-rose-800/50" : "bg-rose-50 border border-rose-200"
        }`}>
          <AlertCircle className="w-5 h-5 text-rose-500" />
          <span className="text-xs text-rose-400">Error al obtener predicción</span>
        </div>
      )}

      {/* Prediction result */}
      {selectedPoint && data && !isLoading && (
        <>
          {/* Main metric */}
          <div className={`rounded-xl p-4 ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-emerald-500" />
              <span className={`text-xs font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                {contaminant === "NO2" ? "NO₂" : contaminant === "SO2" ? "SO₂" : "O₃"} — {horizon}
              </span>
            </div>
            <div className="flex items-end gap-2">
              <span className="mono-value text-3xl font-bold text-emerald-400">
                {data.predicted_value.toFixed(1)}
              </span>
              <span className={`mono-value text-sm pb-1 ${isDark ? "text-slate-400" : "text-slate-500"}`}>
                {meta.unit}
              </span>
            </div>
            <div className={`mono-value text-sm mt-1 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
              ± {data.uncertainty_sigma.toFixed(1)} σ
            </div>
          </div>

          {/* All horizons comparison */}
          <div className={`rounded-xl p-3 ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}>
            <div className={`text-xs font-semibold mb-2 ${isDark ? "text-slate-400" : "text-slate-600"}`}>
              Todos los horizontes
            </div>
            <div className="space-y-2">
              {["T+1", "T+3", "T+7"].map((h) => {
                const val = data.all_horizons?.[h]?.[contaminant];
                return (
                  <div key={h} className="flex items-center justify-between">
                    <span className={`mono-value text-xs px-2 py-0.5 rounded-full ${
                      h === horizon
                        ? "bg-emerald-500 text-white"
                        : isDark
                        ? "bg-slate-700 text-slate-400"
                        : "bg-slate-100 text-slate-500"
                    }`}>
                      {h}
                    </span>
                    <span className={`mono-value text-xs font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                      {val?.toFixed(1) ?? "—"} {meta.unit}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Model info */}
          <div className={`rounded-xl p-3 ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}>
            <div className={`text-xs font-semibold mb-2 ${isDark ? "text-slate-400" : "text-slate-600"}`}>
              Info del modelo
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className={isDark ? "text-slate-500" : "text-slate-400"}>Versión</span>
                <span className={`mono-value ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                  {data.model_version}
                </span>
              </div>
              <div className="flex justify-between">
                <span className={isDark ? "text-slate-500" : "text-slate-400"}>MD5</span>
                <span className={`mono-value ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                  {data.md5_checkpoint?.slice(0, 8)}…
                </span>
              </div>
              <div className="flex justify-between">
                <span className={isDark ? "text-slate-500" : "text-slate-400"}>Timestamp</span>
                <span className={`mono-value ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                  {data.timestamp ? new Date(data.timestamp).toLocaleTimeString("es-CO") : "—"}
                </span>
              </div>
            </div>
          </div>

          {/* Time series chart */}
          <TimeSeriesChart contaminant={contaminant} unit={meta.unit} />

          {/* Download buttons */}
          {selectedPoint && (
            <DownloadButtons
              lat={selectedPoint.lat}
              lon={selectedPoint.lon}
              contaminant={contaminant}
            />
          )}
        </>
      )}
    </aside>
  );
}
