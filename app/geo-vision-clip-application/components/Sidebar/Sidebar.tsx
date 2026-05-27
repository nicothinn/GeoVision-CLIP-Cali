"use client";
import { useState } from "react";
import { Layers, MapPin, Map, Crosshair } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { DAGMA_STATIONS, CONTAMINANT_META } from "@/lib/constants";
import { useStations } from "@/hooks/useStations";
import { Switch } from "@/components/ui/switch";

export function Sidebar() {
  const {
    theme,
    contaminant,
    selectedPoint,
    setPoint,
    clearPoint,
    showBarriosLayers,
    setShowBarriosLayers,
  } = useAppStore();

  const { data: stationsData } = useStations();
  const isDark = theme === "dark";

  const stations = stationsData?.stations ?? DAGMA_STATIONS.map((s) => ({ ...s, last_reading: undefined }));

  // Estado local para inputs de coordenadas
  const [inputLat, setInputLat] = useState(selectedPoint?.lat.toString() ?? "");
  const [inputLon, setInputLon] = useState(selectedPoint?.lon.toString() ?? "");

  const handleSubmitCoords = (e: React.FormEvent) => {
    e.preventDefault();
    const lat = parseFloat(inputLat);
    const lon = parseFloat(inputLon);
    if (!isNaN(lat) && !isNaN(lon)) {
      setPoint(lat, lon);
    }
  };

  const handleClear = () => {
    clearPoint();
    setInputLat("");
    setInputLon("");
  };

  return (
    <aside
      className={`flex flex-col gap-4 p-4 overflow-y-auto ${
        isDark ? "bg-slate-900" : "bg-slate-50"
      } w-64 shrink-0`}
    >
      {/* Selected point info */}
      {selectedPoint && (
        <div className={`rounded-xl p-3 ${
          isDark ? "bg-emerald-500/10 border border-emerald-500/30" : "bg-emerald-50 border border-emerald-200"
        }`}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <MapPin className="w-3.5 h-3.5 text-emerald-500" />
              <span className={`text-xs font-semibold ${isDark ? "text-emerald-400" : "text-emerald-700"}`}>
                Punto seleccionado
              </span>
            </div>
            <button
              onClick={handleClear}
              className={`text-[10px] px-2 py-0.5 rounded ${
                isDark ? "bg-slate-700 text-slate-400 hover:bg-slate-600" : "bg-slate-200 text-slate-500 hover:bg-slate-300"
              }`}
            >
              Limpiar
            </button>
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

      {/* Manual coordinate input */}
      <form
        onSubmit={handleSubmitCoords}
        className={`rounded-xl p-3 ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}
      >
        <div className="flex items-center gap-2 mb-3">
          <Crosshair className="w-3.5 h-3.5 text-emerald-500" />
          <span className={`text-xs font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>
            Ingresar coordenadas
          </span>
        </div>
        <div className="flex gap-2 mb-2">
          <div className="flex-1">
            <label className={`text-[10px] block mb-1 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
              Latitud
            </label>
            <input
              type="number"
              step="any"
              placeholder="ej: 3.4516"
              value={inputLat}
              onChange={(e) => setInputLat(e.target.value)}
              className={`w-full text-xs px-2 py-1.5 rounded-md border ${
                isDark
                  ? "bg-slate-700 border-slate-600 text-slate-200 placeholder-slate-500"
                  : "bg-white border-slate-300 text-slate-800 placeholder-slate-400"
              } font-mono outline-none focus:ring-1 focus:ring-emerald-500`}
            />
          </div>
          <div className="flex-1">
            <label className={`text-[10px] block mb-1 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
              Longitud
            </label>
            <input
              type="number"
              step="any"
              placeholder="ej: -76.5320"
              value={inputLon}
              onChange={(e) => setInputLon(e.target.value)}
              className={`w-full text-xs px-2 py-1.5 rounded-md border ${
                isDark
                  ? "bg-slate-700 border-slate-600 text-slate-200 placeholder-slate-500"
                  : "bg-white border-slate-300 text-slate-800 placeholder-slate-400"
              } font-mono outline-none focus:ring-1 focus:ring-emerald-500`}
            />
          </div>
        </div>
        <button
          type="submit"
          className="w-full text-xs py-1.5 rounded-md font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
        >
          Consultar
        </button>
      </form>

      {/* Límites administrativos */}
      <div className={`rounded-xl p-3 ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <Map className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            <div className="min-w-0">
              <span className={`text-xs font-semibold block ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                Límites administrativos
              </span>
              <span className={`text-[10px] block mt-0.5 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
                Comunas y barrios (hover)
              </span>
            </div>
          </div>
          <Switch
            checked={showBarriosLayers}
            onCheckedChange={setShowBarriosLayers}
            aria-label="Mostrar comunas y barrios en el mapa"
          />
        </div>
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
