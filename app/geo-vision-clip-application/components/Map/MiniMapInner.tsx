"use client";
import { MapContainer, TileLayer } from "react-leaflet";
import { CALI_CENTER, TILE_DARK, TILE_LIGHT, TILE_ATTRIBUTION } from "@/lib/constants";
import { GradientOverlay } from "./GradientOverlay";

interface GridData {
  lats: number[][];
  lons: number[][];
  values: number[][];
  variances: number[][];
}

interface MiniMapInnerProps {
  contaminant: string;
  horizon: string;
  data: GridData | null;
  theme: "dark" | "light";
}

export default function MiniMapInner({ contaminant, horizon, data, theme }: MiniMapInnerProps) {
  const label = contaminant === "NO2" ? "NO₂" : contaminant === "SO2" ? "SO₂" : "O₃";
  return (
    <div className="relative rounded-xl overflow-hidden w-full" style={{ height: "clamp(140px, 18vw, 220px)" }}>
      {/* Floating label */}
      <div className="absolute top-2 left-2 z-[400] bg-slate-900/90 px-2 py-1 rounded-md text-xs font-mono text-emerald-400 pointer-events-none border border-slate-700/50">
        {label}
      </div>
      <MapContainer
        center={CALI_CENTER}
        zoom={11}
        zoomControl={false}
        scrollWheelZoom={false}
        dragging={false}
        doubleClickZoom={false}
        keyboard={false}
        attributionControl={false}
        className="h-full w-full"
        style={{ background: theme === "dark" ? "#0f172a" : "#f8fafc" }}
      >
        <TileLayer url={theme === "dark" ? TILE_DARK : TILE_LIGHT} attribution={TILE_ATTRIBUTION} />
        {data && <GradientOverlay data={data} contaminant={contaminant} />}
      </MapContainer>
    </div>
  );
}
