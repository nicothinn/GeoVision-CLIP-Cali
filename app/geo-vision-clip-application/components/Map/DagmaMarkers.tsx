"use client";
import { CircleMarker, Popup } from "react-leaflet";
import { CONTAMINANT_META } from "@/lib/constants";

interface Station {
  id: number;
  name: string;
  lat: number;
  lon: number;
  zone: string;
  last_reading?: { NO2: number; SO2: number; O3: number };
}

interface DagmaMarkersProps {
  stations: Station[];
  contaminant: string;
}

export function DagmaMarkers({ stations, contaminant }: DagmaMarkersProps) {
  if (!stations.length) return null;

  return (
    <>
      {stations.map((station) => {
        const reading = station.last_reading?.[contaminant as keyof typeof station.last_reading];
        const meta = CONTAMINANT_META[contaminant];

        return (
          <CircleMarker
            key={station.id}
            center={[station.lat, station.lon]}
            radius={8}
            pathOptions={{
              color: "#10b981",
              fillColor: "#10b981",
              fillOpacity: 0.9,
              weight: 2,
            }}
          >
            <Popup>
              <div className="min-w-[180px]">
                <div className="font-semibold text-emerald-400 text-sm mb-2">
                  {station.name}
                </div>
                <div className="text-xs text-slate-400 mb-2">Zona: {station.zone}</div>
                {station.last_reading && (
                  <div className="space-y-1">
                    {(["NO2", "SO2", "O3"] as const).map((c) => (
                      <div key={c} className="flex justify-between text-xs">
                        <span className={`font-mono ${c === contaminant ? "text-emerald-400 font-semibold" : "text-slate-400"}`}>
                          {c}
                        </span>
                        <span className="font-mono text-slate-200">
                          {station.last_reading![c].toFixed(1)} {CONTAMINANT_META[c].unit}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                {reading !== undefined && (
                  <div className="mt-2 pt-2 border-t border-slate-700 text-xs text-slate-500">
                    Lectura actual seleccionada: {reading.toFixed(1)} {meta?.unit}
                  </div>
                )}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
}
