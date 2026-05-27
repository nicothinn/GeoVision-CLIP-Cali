"use client";
import { useEffect } from "react";
import { MapContainer, TileLayer, useMapEvents, useMap } from "react-leaflet";
import { CALI_CENTER, TILE_DARK, TILE_LIGHT, TILE_ATTRIBUTION } from "@/lib/constants";
import { DagmaMarkers } from "./DagmaMarkers";
import { AqiLegend } from "./AqiLegend";
import { BarriosOverlay } from "./BarriosOverlay";
import { useBarriosGeo } from "@/hooks/useBarriosGeo";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix leaflet default icon path issue in Next.js
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

interface CaliMapInnerProps {
  theme: "dark" | "light";
  contaminant: string;
  showBarriosLayers: boolean;
  onPointClick: (lat: number, lon: number) => void;
  stations: Array<{
    id: number;
    name: string;
    lat: number;
    lon: number;
    zone: string;
    last_reading?: { NO2: number; SO2: number; O3: number };
  }>;
}

function ClickHandler({ onPointClick }: { onPointClick: (lat: number, lon: number) => void }) {
  useMapEvents({
    click: (e) => onPointClick(e.latlng.lat, e.latlng.lng),
  });
  return null;
}

function TileUpdater({ theme }: { theme: "dark" | "light" }) {
  const map = useMap();
  useEffect(() => {
    map.eachLayer((layer) => {
      if ((layer as L.TileLayer).setUrl) {
        (layer as L.TileLayer).setUrl(theme === "dark" ? TILE_DARK : TILE_LIGHT);
      }
    });
  }, [theme, map]);
  return null;
}

function BarriosLayers({
  theme,
  showBarriosLayers,
}: {
  theme: "dark" | "light";
  showBarriosLayers: boolean;
}) {
  const { data } = useBarriosGeo(showBarriosLayers);
  if (!showBarriosLayers || !data) return null;
  return (
    <BarriosOverlay
      barrios={data.barrios}
      comunas={data.comunas}
      theme={theme}
    />
  );
}

export default function CaliMapInner({
  theme,
  contaminant,
  showBarriosLayers,
  onPointClick,
  stations,
}: CaliMapInnerProps) {
  const tileUrl = theme === "dark" ? TILE_DARK : TILE_LIGHT;

  return (
    <MapContainer
      center={CALI_CENTER}
      zoom={12}
      className="h-full w-full rounded-xl"
      style={{ background: theme === "dark" ? "#0f172a" : "#f8fafc" }}
    >
      <TileLayer url={tileUrl} attribution={TILE_ATTRIBUTION} />
      <TileUpdater theme={theme} />
      <ClickHandler onPointClick={onPointClick} />
      <DagmaMarkers stations={stations} contaminant={contaminant} />
      <BarriosLayers theme={theme} showBarriosLayers={showBarriosLayers} />
      <AqiLegend theme={theme} />
    </MapContainer>
  );
}
