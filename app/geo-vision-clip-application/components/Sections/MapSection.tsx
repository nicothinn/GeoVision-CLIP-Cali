"use client";
import { useCallback } from "react";
import { MapPin, Loader2 } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { useStations } from "@/hooks/useStations";
import { usePrediction } from "@/hooks/usePrediction";
import { useScrollReveal } from "@/hooks/useScrollReveal";
import { Sidebar } from "@/components/Sidebar/Sidebar";
import { PredictionPanel } from "@/components/Dashboard/PredictionPanel";
import { HorizonSlider } from "@/components/Controls/HorizonSlider";
import dynamic from "next/dynamic";

const CaliMapInner = dynamic(() => import("@/components/Map/CaliMapInner"), {
  ssr: false,
  loading: () => (
    <div className="flex flex-col items-center justify-center h-full bg-slate-900 gap-3">
      <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
      <span className="text-slate-500 text-sm font-mono">Inicializando mapa...</span>
    </div>
  ),
});

function MapCore() {
  const { theme, contaminant, radiusKm, selectedPoint, setPoint, showBarriosLayers } = useAppStore();
  const { data: stationsData } = useStations();
  const { data: prediction } = usePrediction({
    lat: selectedPoint?.lat ?? null,
    lon: selectedPoint?.lon ?? null,
    radiusKm,
    contaminant,
    horizon: "T+1",
  });

  const stations = stationsData?.stations ?? [];

  const handlePointClick = useCallback(
    (lat: number, lon: number) => setPoint(lat, lon),
    [setPoint]
  );

  return (
    <CaliMapInner
      theme={theme}
      gradientData={prediction?.grid ?? null}
      contaminant={contaminant}
      showBarriosLayers={showBarriosLayers}
      onPointClick={handlePointClick}
      stations={stations}
    />
  );
}

export function MapSection() {
  const { theme, selectedPoint } = useAppStore();
  const isDark = theme === "dark";

  const { ref, visible } = useScrollReveal(0.05);

  return (
    <section
      id="mapa"
      ref={ref as React.RefObject<HTMLElement>}
      className={`relative w-full ${isDark ? "bg-slate-900" : "bg-slate-50"}`}
    >
      {/* Section header */}
      <div className={`reveal ${visible ? "visible" : ""} px-6 md:px-10 pt-16 pb-6`}>
        <div className="flex items-center gap-3 mb-3">
          <div className="section-divider w-8" />
          <span className={`text-xs font-mono uppercase tracking-widest ${isDark ? "text-emerald-500" : "text-emerald-600"}`}>
            Mapa interactivo
          </span>
        </div>
        <h2 className={`text-2xl sm:text-3xl font-bold text-balance ${isDark ? "text-slate-100" : "text-slate-900"}`}>
          Distribucion espacial de contaminantes
        </h2>
        <p className={`mt-2 text-sm leading-relaxed max-w-xl ${isDark ? "text-slate-400" : "text-slate-500"}`}>
          Haz clic en cualquier punto del mapa de Cali, o ingresa coordenadas
          manualmente en la barra lateral, para obtener una prediccion
          localizada de contaminantes atmosfericos.
        </p>
      </div>

      {/* Map + panels layout */}
      <div
        className={`reveal reveal-delay-2 ${visible ? "visible" : ""} flex flex-col lg:flex-row gap-0 border-t ${
          isDark ? "border-slate-800" : "border-slate-200"
        }`}
      >
        {/* Left sidebar */}
        <div className={`lg:w-64 shrink-0 border-r ${isDark ? "border-slate-800" : "border-slate-200"}`}>
          <Sidebar />
        </div>

        {/* Center map */}
        <main className="flex-1 flex flex-col min-h-0">
          {/* Map canvas — fixed tall height so it feels immersive */}
          <div className="relative" style={{ height: "clamp(400px, 60vh, 700px)" }}>
            {!selectedPoint && (
              <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] pointer-events-none">
                <div className="flex items-center gap-2 px-3 py-2 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700/50">
                  <MapPin className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="text-xs text-slate-300 font-mono">
                    Haz clic en Cali para predecir contaminantes
                  </span>
                </div>
              </div>
            )}
            <MapCore />
          </div>

          {/* Timeline slider */}
          <HorizonSlider />
        </main>

        {/* Right prediction panel */}
        <div className={`lg:w-72 shrink-0 border-l ${isDark ? "border-slate-800" : "border-slate-200"}`}>
          <PredictionPanel />
        </div>
      </div>
    </section>
  );
}
